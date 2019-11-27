# import sys, os, json, random, argparse, time
# import numpy as np
# import matplotlib.pyplot as plt


# from pymoo.algorithms.nsga2 import NSGA2
# from pymoo.optimize import minimize

# from state import State
# import districts
# import metrics
# from constraints import fix_pop_equality
# import mutation

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description='')
#     parser.add_argument('-d', '--n_districts', default=5, type=int)
#     parser.add_argument('-t', '--n_tiles', default=100, type=int)
#     parser.add_argument('-p', '--pop_size', default=100, type=int)
#     parser.add_argument('-g', '--n_gens', default=100, type=int)
#     parser.add_argument('-o', '--out', required=True)
#     args = parser.parse_args()

#     states = [ State.makeRandom(args.n_tiles) ]
#     while states[-1].n_tiles > 300:
#         states.append(states[-1].contract())

#     state = states[-1]

#     # print(states)
#     # exit()
#     # state = State.makeRandom(args.n_tiles).contract()
#     # state = State.fromFile('state.json')

#     ############################################################################
#     seeds = []
#     print('Creating initial population.')
#     with tqdm(total=args.pop_size) as pbar:
#         while len(seeds) < args.pop_size:
#             try:
#                 p = districts.make_random(state, args.n_districts)
#                 fix_pop_equality(state, p, args.n_districts, tolerance=.10, max_iters=600)
#                 seeds.append(p)
#                 pbar.update(1)
#             except ValueError as e:
#                 pass
#             except StopIteration as e:
#                 pass
#     print('Created seeds')
#     ############################################################################

#     algorithm = NSGA2(
#         pop_size=args.pop_size,
#         sampling=np.array(seeds),
#         crossover=DistrictCross(),
#         mutation=DistrictMutation(state, args.n_districts),
#     )

#     used_metrics  = {
#         'Efficiency-Gap': metrics.efficiency_gap,
#         'Compactness': metrics.compactness,
#         'Competitiveness': metrics.competitiveness
#     }

#     # phases = [
#     #     ['division_3']
#     # ]

#     problem = DistrictProblem(
#         state,
#         args.n_districts,
#         used_metrics.values()
#     )

#     res = minimize(
#         problem,
#         algorithm,
#         ('n_gen', args.n_gens),
#         seed=1,
#         verbose=False,
#         save_history=False
#     )

#     with open(os.path.join(args.out, 'rundata.json'), 'w') as f:
#         json.dump({
#             'n_districts': args.n_districts,
#             'nsga_config': {},
#             'state': state.toJSON(),
#             'values': res.F.tolist(),
#             'solutions': res.X.tolist(),
#             'metrics' : list(used_metrics.keys()),
#             'metrics_data': {
#                 'lost_votes': [
#                     np.asarray(metrics.lost_votes(state, x, args.n_districts)).tolist()
#                     for x in res.X
#                 ]
#             }

#         }, f)

#     # plt.scatter(res.F[:, 0], res.F[:, 1])
#     # plt.savefig(os.path.join(args.out, 'pareto_front.png'))
#     # pop_each_gen = [ a.pop for a in res.history[1:] ]
#     # obj_and_feasible_each_gen = [pop[pop.get("feasible")[:,0]].get("F") for pop in pop_each_gen]
#     # hv = [ metric.calc(f) for f in obj_and_feasible_each_gen ]
#     # plt.plot(np.arange(len(hv)), hv, '-o')
#     # plt.title("Convergence")
#     # plt.xlabel("Generation")
#     # plt.ylabel("Hypervolume")
#     # plt.savefig(os.path.join(args.out, 'convergence.png'))
