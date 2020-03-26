from pdb import set_trace as bb
from pymoo.operators.selection.tournament_selection import compare, TournamentSelection
from pymoo.util.dominator import Dominator
from pymoo.algorithms.nsga2 import NSGA2
from pymoo.factory import get_problem
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
from pymoo.model.algorithm import Algorithm
from pymoo.factory import get_termination
from pymoo.model.termination import Termination
from pymoo.problems.multi.tnk import TNK
import numpy as np

import autograd.numpy as anp
from pymoo.problems.util import load_pareto_front_from_file
from pymoo.model.problem import Problem

#version of binary tournament for NSGA2 offspring-generation that is agnostic to constraint-violation
#for infeasible pop
def cv_agnostic_binary_tournament(pop, P, algorithm, **kwargs):
    if P.shape[1] != 2:
        raise ValueError("Only implemented for binary tournament!")

    tournament_type = algorithm.tournament_type
    S = np.full(P.shape[0], np.nan)

    for i in range(P.shape[0]):

        a, b = P[i, 0], P[i, 1]

        # if at least one solution is infeasible
        if False: #pop[a].CV > 0.0 or pop[b].CV > 0.0:
            S[i] = compare(a, pop[a].CV, b, pop[b].CV, method='smaller_is_better', return_random_if_equal=True)

        # both solutions are feasible
        else:

            if tournament_type == 'comp_by_dom_and_crowding':
                rel = Dominator.get_relation(pop[a].F, pop[b].F)
                if rel == 1:
                    S[i] = a
                elif rel == -1:
                    S[i] = b

            elif tournament_type == 'comp_by_rank_and_crowding':
                S[i] = compare(a, pop[a].rank, b, pop[b].rank,
                               method='smaller_is_better')

            else:
                raise Exception("Unknown tournament type.")

            # if rank or domination relation didn't make a decision compare by crowding
            if np.isnan(S[i]):
                S[i] = compare(a, pop[a].get("crowding"), b, pop[b].get("crowding"),
                               method='larger_is_better', return_random_if_equal=True)

    return S[:, None].astype(np.int, copy=False)


#mix-in class to modify a problem to cache full objectives
class FI_problem_mixin(object):
    def _evaluate(self,x,out,*args,**kwargs):
        super()._evaluate(x,out,*args,**kwargs)
        #cache original objective values, so we can mask later
        out["_F"]=out["F"]

#mix-in class to modify an algorithm (only tested for NSGA2) to be subalgorithms for F-IF search
class FI_algo_mixin(object):
    def initialize(self,problem,mask,**kwargs):
        #each sub search algorithm can take in a mask that will mask out some of the objectives
        #that way, infeasible can be guided towards e.g. feasibility + novelty; while feasible pop can focus on other objectives
        self.mask = mask
        self.hv_history = []
        self.pop_size_history = []
        super().initialize(problem,**kwargs)

    #helper function to create masked fitness values (a view of metrics for a particular sub-population)
    def mask_fitness(self):
        #potentially mask out undesired objectives, to make selection
        #in F and IF pop different
        if self.mask!=None:
            for i in range(len(self.pop)):
                self.pop[i].F = self.pop[i].get("_F")[self.mask]

    #modifies the main Genetic Algorithm loop to be of service for 2POP search
    def _next(self):
        self.mask_fitness()

        # do the mating using the current population
        self.off = self._mating(self.pop)#, n_max_iterations=100)

        # if the mating could not generate any new offspring (duplicate elimination might make that happen)
        if len(self.off) == 0:
            self.termination.force_termination = True
            return
        # if not the desired number of offspring could be created
        elif len(self.off) < self.n_offsprings:
            if self.verbose:
                print("WARNING: Mating could not produce the required number of (unique) offsprings!")

        # evaluate the offspring
        # print('in _next', self.off.shape, self.pop.get("F").shape, self.pop.get("F").sum(axis=0))
        self.evaluator.eval(self.problem, self.off, algorithm=self)

        # separate offspring into feasible, infeasible
        self.feasible = self.off[self.off.get("feasible")[:, 0]]
        self.infeasible = self.off[np.logical_not(self.off.get("feasible")[:,0])]

        # separate population into feasible, infeasible (only should matter for first iteration of algo..)
        self.feasible_pop = self.pop[self.pop.get("feasible")[:,0]]
        self.infeasible_pop = self.pop[np.logical_not(self.pop.get("feasible")[:,0])]

        # we do not set up the next population (i.e. non-dominated sorting etc.) -- that will be handled by the meta-2pop Algorithm

#create version of NSGA2 with the mixin
class NSGA2_FI(FI_algo_mixin,NSGA2):
    pass

#main algorithm that implements feasible-infeasible search
#takes as params a search algorithm to be used for the feasible pop, and one to be used for infeasible pop
class FI_Algo(Algorithm):
    def initialize(self,
                   feas_algo,
                   infeas_algo,
                   termination,
                   **kwargs):

        super().__init__(**kwargs)

        #assign both of the underlying algorithms
        self.feas_algo = feas_algo
        self.infeas_algo = infeas_algo
        self.termination = termination

    def _initialize(self):
        #initialize each subalgorithm
        for algo in [self.feas_algo,self.infeas_algo]:
            algo.n_gen = 1
            algo._initialize()
            # algo._each_iteration(algo, first=True)

        #HACK: should be set in constructor for NSGA2 survival
        #this allows NSGA2 in infeasible pop to do mutliobjective search e.g. constraint-satisfaction + novelty
        self.infeas_algo.survival.filter_infeasible=False

    def _next(self):
        feas_algo = self.feas_algo
        infeas_algo = self.infeas_algo
        #run each algorithm to generate offspring
        for algo in [self.feas_algo, self.infeas_algo]:
            #as long as the population is not empty (i.e. in the beginning of search for feasible pop)
            if len(algo.pop) > 0:   #TODO: instead, try seed to generate random new individuals
                algo.next()

        #aggregate feasible and infeasible offspring
        feas_off_total = self.feas_algo.feasible.merge(self.infeas_algo.feasible)
        infeas_off_total = self.feas_algo.infeasible.merge(self.infeas_algo.infeasible)

        #aggregate feasible and infeasible subpopulations
        feas_pop_total = self.feas_algo.feasible_pop.merge(self.infeas_algo.feasible_pop)
        infeas_pop_total = self.infeas_algo.infeasible_pop.merge(self.feas_algo.infeasible_pop)

        #aggregate total feasible and infeasible individuals
        feas_total = feas_pop_total.merge(feas_off_total)
        infeas_total = infeas_pop_total.merge(infeas_off_total)

        feas_algo.pop = feas_total
        infeas_algo.pop = infeas_total

        #mask fitnesses before doing selection (i.e. make sure each algo is doing selection based on its preferred objectives)
        feas_algo.mask_fitness()
        infeas_algo.mask_fitness()

        #do selection to form new populations
        if len(feas_algo.pop) > 0:   #feasible pop may sometimes have no members (at beginning of search)
            feas_algo.pop = feas_algo.survival.do(feas_algo.problem, feas_algo.pop, feas_algo.pop_size, algorithm=feas_algo)
        infeas_algo.pop = infeas_algo.survival.do(infeas_algo.problem, infeas_algo.pop, infeas_algo.pop_size, algorithm=infeas_algo)

        #log population size
        # feas_algo.pop_size_history.append(len(feas_algo.pop))
        # infeas_algo.pop_size_history.append(len(infeas_algo.pop))

        #set the reported pop for this 2POP algorithm to be the feasible individuals
        self.pop = feas_algo.pop

        # bb()


#new minimize call that works for feas/infeasible search
#takes as input a problem, search algo for feasible + infeasible populations, and masks for objective functions
def FI_minimize(problem,feas_algo,infeas_algo,termination, feas_mask=None,infeas_mask=None,**kwargs):

    # create a copy of the algorithm object to ensure no side-effects
    # algorithm = copy.deepcopy(algorithm)

    # set the termination criterion and store it in the algorithm object
    if termination is None:
        termination = None
    elif not isinstance(termination, Termination):
        if isinstance(termination, str):
            termination = get_termination(termination)
        else:
            termination = get_termination(*termination)

    # initialize the method given a problem
    feas_algo.initialize(problem,feas_mask,
                         termination=termination,
                         **kwargs)

    infeas_algo.initialize(problem,infeas_mask,
                         termination=termination,
                         **kwargs)

    #create feasible-infeasible algorithm
    f_if = FI_Algo()
    #initialize it
    # print('termination', termination)
    # print(kwargs)
    f_if.initialize(feas_algo,infeas_algo, problem=problem, termination=termination, **kwargs)
    # print(f_if.termination)
    #run solver
    res = f_if.solve()
    res.algorithm = f_if

    return res


