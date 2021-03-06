import numpy as np
import random
from SoccerMDP import *
from MultiQ_agent import *
from helpers import *
from get_uCorrelatedEquilibrium import get_uCE
import time

starttime=time.time()
def get_dS(state, stateSpace):
    posA, posB, playerWithBall = state
    dS = encode((posA[0], posA[1], posB[0], posB[1], playerWithBall), stateSpace)  # discretize state
    return dS

Nplayers=2  # TODO: currently hard coded in Soccer environment as well. In future, try to generalize it.
Nrows=2
Ncols=2
Duals=2 # number of states possible for each position of a players
stateSpace=(Nrows, Ncols, Nrows, Ncols, Duals)
Nstates=np.cumprod(stateSpace)[-1]

End=1000000
decay=0.01**(1/(End*1.0))
gamma=0.9
actionExplorationParams={'eps': 0.2, 'End': End,
                        't1': 300.0, 'tEnd': 0.1,
                        'eps1': 1.0, 'epsEnd': 0.01}


env=Soccer(rows=Nrows, cols=Ncols,
            goalposA=np.asarray([(i, -1)    for i in range(0, Nrows)], dtype=int),
            goalposB=np.asarray([(i, Ncols) for i in range(0, Nrows)], dtype=int),
            defaultPosA=[0, 1], defaultPosB=[0, 0], defaultBallWith='B')

envActionMap=env.getActionMap()                    # get action map
actionSpace=(len(envActionMap), len(envActionMap))    # create action space. Both players have same number of actions.
Nactions=np.cumprod(actionSpace)[-1]            # get number of joint actions (exponential in numner of players)
monitoractA_name='S'; monitoractB_name='stand'  # get joint action to be monitored for Q convergence

multiAgent=MultiQ_agent(Nplayers=2, Nstates=Nstates, actionSpace=actionSpace, actionExplorationParams=actionExplorationParams)
actionSelection=multiAgent.eGreedyAction

#---Initialize
s=env.reset()               # reset environment
ds=get_dS(s, stateSpace)    # discretize state

#---Set monitors
monitorState=ds             # state to be monitored for Q convergence
for actNum, actName in envActionMap.iteritems():
    if monitoractA_name==actName:   monitoractA_num=actNum
    if monitoractB_name==actName:   monitoractB_num=actNum
monitorAction=encode((monitoractA_num, monitoractB_num), actionSpace)
monitorPlayer=env.playersDict['A']
Qmonitor=[]
#-----------

multiAgent.makeUpdates()  # initialize agent params
_, actionDistribution=multiAgent.get_V_and_ActionDistribution(ds, get_uCE)
actA, actB = actionSelection(actionDistribution)
alpha=1.0
#---------

for iteration in range(End):
    # print "{0}\n{1} {2}\n".format(s, actionMap[actA], actionMap[actB])
    sprime, rewards, done=env.step((envActionMap[actA], envActionMap[actB]))      # take step in environment
    dsprime = get_dS(sprime, stateSpace)                                    # discretize state
    Vsprime, _=multiAgent.get_V_and_ActionDistribution(dsprime, get_uCE) # get next state value and action distribution based on current Q table
    jointAction=encode((actA, actB), actionSpace)

    if done:
        for player in range(Nplayers):
            multiAgent.Q[player, ds, jointAction]=\
                (1-alpha)*multiAgent.Q[player, ds, jointAction] + alpha * (rewards[player])
        s=env.reset()               # reset environment
        ds=get_dS(s, stateSpace)    # discretize state

    else:
        for player in range(Nplayers):
            multiAgent.Q[player, ds, jointAction]=\
                (1-alpha)*multiAgent.Q[player, ds, jointAction] + alpha * (rewards[player] + gamma * Vsprime[player])
        s=sprime; ds=dsprime

    _, actionDistribution = multiAgent.get_V_and_ActionDistribution(ds, get_uCE)
    multiAgent.makeUpdates()  # prepare agent for next episode
    alpha *= decay
    actA, actB = actionSelection(actionDistribution)
    Qmonitor.append(multiAgent.Q[monitorPlayer, monitorState, monitorAction])

Qmonitor=np.asarray(Qmonitor, dtype=float)
Qdiff=np.absolute(Qmonitor[1:] - Qmonitor[0:-1])

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.plot(Qdiff)
plt.ylim(0.0, 0.5)
plt.yticks(np.linspace(0,0.5, num=11))
plt.savefig('CorrelatedQ_2LPcalls.png')

endtime=time.time()
print '\n\t --> total run time={0}s <--'.format(endtime-starttime)

