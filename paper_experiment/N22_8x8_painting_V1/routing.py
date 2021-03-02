
import math
import random

import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Categorical


from libs import init,Get_Neighborhood,Get_detailed_data,find_start_task,get_sorted_dict,ActorCritic,Get_full_route_by_XY,Get_reward_by_pendTimes,Actor,Critic,computeContention,Update_link_set,Check_if_Done_improved,Environment_improved
from queue import Queue
import copy





class link_item():#可以根据在list中的下标索引到它连接的是哪两个PE
    def __init__(self):
        #记录这个link的timeline，list中的每个元素是list，形式为[task_source,task_dest,start_time,end_time]
        self.timeline=[]
    

#adj_matrix里task的编号是从1开始的，execution和MapResult也是从1开始编号
def improved_routeCompute(adj_matrix,num_of_tasks,execution,num_of_rows,MapResult):
    #初始化
    task_graph={}
    link_set=[]
    receiveMatrix = [-1]
    total_link_num=(num_of_rows-1+num_of_rows)*(num_of_rows-1)+num_of_rows-1
    for i in range(0,total_link_num):
        tmp=link_item()
        link_set.append(tmp)
    for i in range(1,num_of_tasks+1):#初始化receive_matrix，这里遍历的是每一列
        total_receive_for_i=0
        for j in range(1,num_of_tasks+1):
            total_receive_for_i+=adj_matrix[j][i]
        receiveMatrix.append(total_receive_for_i)
    

    total_contention_times=0
    edge_queue=[]#每个item为( 'task_source,task_dest' , end time of task_source )，如('1,2',20)，task的编号从1开始
    #添加一开始就能执行的边
    for i in range(1,num_of_tasks+1):
        if(receiveMatrix[i]==0):#这个task可以立刻执行，然后开始传输
            for j in range(1,num_of_tasks+1):
                if(adj_matrix[i][j]!=0):
                    tmp=(str(i)+','+str(j),execution[i])
                    edge_queue.append(tmp)
    edge_queue.sort(key=lambda x: x[1])#按照task_source的结束时间排序

    use_cuda = torch.cuda.is_available()
    device   = torch.device("cuda" if use_cuda else "cpu")
    #初始化结束

    #队列不空时，取队首的边来执行，将这条边以及link_set传入RL模型，RL模型还是step-by-step来计算每一步应该怎么走，但是计算reward的时候，就只需要检查在这些由RL模型计算出的link上，发生的最长的争用，然后将它作为这一步的reward就好了
    #而检查指定的link的争用情况，只需要检查link在[task_source的结束时间,task_source的结束时间+transmission]时间段是否可用，如果可用的话就占用这个时间段的这些link，如果不可用，则等待时间T，直到[task_source的结束时间+T,task_source的结束时间+T+transmission]，而这个时间T就是这条link上的contention
    #RL模型训练结束后，记录在训练过程中出现的最好的route，作为这条edge的route
    while(len(edge_queue)!=0):
        current_edge=edge_queue[0]
        edge_queue.pop(0)
        current_source_task=int(current_edge[0].split(',')[0])
        current_dest_task=int(current_edge[0].split(',')[1])
        start_time=current_edge[1]#这条边的预计传输开始时间，也就是source_task的预计结束时间
        current_transmission=adj_matrix[current_source_task][current_dest_task]
        end_time=start_time+current_transmission#这条边的预计传输结束时间，也就是dest_task的预计开始时间

        #向task_graph中添加这条边以及两个任务节点
        if(str(current_source_task) not in task_graph.keys()):#task_source不在task graph中
            task_graph.update({str(current_source_task):{'out_links':[[str(current_dest_task),current_transmission,[],0,0,-1]]}})
        else:#task_source在task graph中，仅需要更新出边及相应参数
            task_graph[str(current_source_task)]['out_links'].append([str(current_dest_task),current_transmission,[],0,0,-1])
        if(str(current_dest_task) not in task_graph.keys()):#task_dest不在task graph中
            task_graph.update({str(current_dest_task):{'out_links':[]}})
        

        #开始为边current_source_task->current_dest_task计算路由
        #state_tensor的四个channel,从0-3以此为N,S,W,E
        #print("now visit edge:",current_source_task,"->",current_dest_task)
        state_tensor=torch.Tensor(np.zeros((1,4,num_of_rows*num_of_rows),dtype=np.int)).to(device)
        state=[state_tensor,MapResult[current_source_task],[]]#state为[state_tensor,cur_position,partRoute]
        best_Route=[]#这条边的最佳路由
        #确保当前的state(map后的位置)不是end state，至少能执行一次action
        tmp_state,_,tmp_done=Check_if_Done_improved(state,MapResult[current_source_task],MapResult[current_dest_task],link_set,num_of_rows,start_time,end_time)
        if(tmp_done):#这两个task的位置无需计算route，直接结束，将结果存储到best_Route
            best_Route=tmp_state[2]
        else:#需要进行RL学习来计算best_Route
            actor=Actor(4,num_of_rows*num_of_rows,2).to(device)
            critic=Critic(4,num_of_rows*num_of_rows).to(device)
            adam_actor=optim.Adam(actor.parameters(),lr=1e-3)
            adam_critic=optim.Adam(critic.parameters(), lr=1e-3)
            gamma=0.99
            
            best_reward=-9999999
            for _ in range(100):
                done=False
                total_reward=0
                state_tensor=torch.Tensor(np.zeros((1,4,num_of_rows*num_of_rows),dtype=np.int)).to(device)
                state=[state_tensor,MapResult[current_source_task],[]]#state为[state_tensor,cur_position,partRoute]

                while not done:
                    state[0]=state[0].to(device)
                    probs=actor(state[0])
                    dist = torch.distributions.Categorical(probs=probs)
                    action = dist.sample()

                    next_state,reward,done=Environment_improved(state,int(action),MapResult[current_source_task],MapResult[current_dest_task],link_set,num_of_rows,start_time,end_time)
                    d=0
                    next_state[0]=next_state[0].to(device)
                    if(done):
                        d=1
                    advantage=reward+(1-d)*gamma*critic(next_state[0])-critic(state[0])

                    total_reward+=reward
                    state=next_state

                    critic_loss = advantage.pow(2).mean()
                    adam_critic.zero_grad()
                    critic_loss.backward()
                    adam_critic.step()

                    actor_loss = -dist.log_prob(action)*advantage.detach()
                    adam_actor.zero_grad()
                    actor_loss.backward()
                    adam_actor.step()

                if(total_reward>best_reward):
                    best_reward=total_reward
                    best_Route=state[2]
        #至此，这条边的route计算完毕，这条边根据best_Route来传输，首先根据这个route来计算出它的等待时间，得到实际的传输时间区间，然后更新link_set和task_graph，然后将这一步的争用次数加到总的争用次数上，再检查这条边执行完毕后是否有新的边可以执行
        current_contention_times=computeContention(best_Route,link_set,num_of_rows,start_time,transmission=current_transmission)
        total_contention_times+=current_contention_times
        Update_link_set(best_Route,link_set,num_of_rows,start_time+current_contention_times,end_time+current_contention_times)
        #更新task_graph
        for i in range(0,len(task_graph[str(current_source_task)]['out_links'])):
            if(int(task_graph[str(current_source_task)]['out_links'][i][0])==current_dest_task):
                task_graph[str(current_source_task)]['out_links'][i][2]=best_Route
        #传输结束后，需要计算是否有新的边可以加入队列
        receiveMatrix[current_dest_task]-=current_transmission
        if(receiveMatrix[current_dest_task]==0):#task_dest已经可以执行，那么将它的出边加入到队列中
            for i in range(1,num_of_tasks+1):
                if(adj_matrix[current_dest_task][i]!=0):
                    edge_queue.append( (str(current_dest_task)+','+str(i) , end_time+current_contention_times+execution[current_dest_task]) )#task_dest的结束时间，应当是source->dest的出边传输结束时间再加上task_dest的执行时间
            edge_queue.sort(key=lambda x: x[1])
    
    return total_contention_times,task_graph
        

            
        

 






if __name__ == '__main__':

    hyperperiod,num_of_tasks,edges,comp_cost=init('./task graph/N4_test.tgff')
    adj_matrix,total_needSend,total_needReceive,execution=Get_detailed_data(num_of_tasks,edges,comp_cost)
    #print(adj_matrix)
    num_of_rows=4
    MapResult=[-1,5,11,2,15]

    contention,task_graph=improved_routeCompute(adj_matrix,num_of_tasks,execution,num_of_rows,MapResult)
    print(contention)
    print(task_graph)






