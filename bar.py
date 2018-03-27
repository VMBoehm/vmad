from vmad import Builder, autooperator
from vmad.lib import fastpm, mpi, linalg
from vmad.contrib import cosmo4d

from abopt.trustregion import TrustRegionCG

import numpy

from abopt.lbfgs import LBFGS

from abopt.abopt2 import real_vector_space, Problem, VectorSpace

from nbodykit.cosmology import Planck15, LinearPower

pm = cosmo4d.ParticleMesh([32, 32, 32], BoxSize=400.)
powerspectrum = LinearPower(Planck15, 0)

wn = pm.generate_whitenoise(555, unitary=True)
x = wn[...]

x = numpy.stack([x.real, x.imag], -1)

ForwardModelHyperParameters = dict(
            q = pm.generate_uniform_particle_grid(),
            stages=[],
            cosmology=Planck15,
            powerspectrum=powerspectrum,
            pm=pm)

ForwardOperator = cosmo4d.FastPMOperator.bind(**ForwardModelHyperParameters)

d, wn, s = ForwardOperator.build().compute(('fs', 'wn', 's'), init=dict(x=x))
print(d, wn, s)
problem = cosmo4d.ChiSquareProblem(pm.comm,
        ForwardOperator,
        [
            cosmo4d.LNResidualOperator.bind(),
#            cosmo4d.NLResidualOperator.bind(d=d[...].sum(axis=-1)),
            cosmo4d.NLResidualOperator.bind(d=d),
        ]
        )

problem.maxradius = 100
problem.initradus = 1
problem.cg_rtol = 0.1
problem.cg_maxiter= 10
trcg = TrustRegionCG()
trcg.cg_monitor = print

lbfgs = LBFGS(maxiter=30)
print(d.cmean(), wn.cmean(), s.c2r().cmean())
print('objective =', problem.f(x))
print((wn ** 2).csum())
#print('gradient = ', problem.g(x))
#print('hessian vector product = ', problem.hessian_vector_product(x, x))
print('hessian vector product = ', problem.hessian_vector_product(x, x).shape)
"""
x1 = lbfgs.minimize(problem, x * 0.001, monitor=print)
x1 = trcg.minimize(problem, x1['x'], monitor=print)
"""
#x1 = lbfgs.minimize(problem, x * 0.001, monitor=print)
x1 = trcg.minimize(problem, x * 0.001, monitor=print)
