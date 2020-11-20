from libs import init,Get_detailed_data
import numpy as np
import json
import os
import datetime


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)

#MapResults里task的编号从0开始，包含路由的task_graph的编号从1开始
def handle_my_output(tg_file_name,MapResults,task_graph,computation_ability):
    hyperperiod,num_of_tasks,edges,comp_cost=init(tg_file_name)
    adj_matrix,total_needSend,total_needReceive,execution=Get_detailed_data(num_of_tasks,edges,comp_cost)
    ret_task_graph={}#任务编号从0开始，包括key和out_links
    for i in task_graph.keys():
        ret_task_graph.update({})
        task_graph[i].update({'input_links':[]})
        task_graph[i].update({'start_time':0})
        task_graph[i].update({'visited':0})
        task_graph[i].update({'total_needSend':total_needSend[int(i)]})
        task_graph[i].update({'end_time':0})
        task_graph[i].update({'total_needReceive':total_needReceive[int(i)]})
        mapto=MapResults[int(i)-1]
        task_graph[i].update({'mapto':mapto})
        task_graph[i].update({'exe_time':computation_ability[int(i)-1][mapto]})
        #处理out_link
        for j in range(len(task_graph[i]['out_links'])):
            task_graph[i]['out_links'][j][0]=int(task_graph[i]['out_links'][j][0])
            task_graph[i]['out_links'][j].insert(2,[])
            task_graph[i]['out_links'][j][3]=[ task_graph[i]['out_links'][j][3] ]
            task_graph[i]['out_links'][j][-2]=mapto
            dest_position=MapResults[task_graph[i]['out_links'][j][0]-1]
            task_graph[i]['out_links'][j][-1]=dest_position
            task_graph[i]['out_links'][j]=[ task_graph[i]['out_links'][j] ]
            #task_graph[i]['out_links'][j].append(0)
    
    #将task的编号改成从0开始，包括key和out_link里的task
    for i in task_graph.keys():
        cur_key=str(int(i)-1)
        ret_task_graph.update({cur_key:task_graph[i]})
        for j in range(len(ret_task_graph[cur_key]['out_links'])):
            ret_task_graph[cur_key]['out_links'][j][0][0]-=1
    
    """
    with open(output_file_name,"w") as f:
        f.write(json.dumps(ret_task_graph,cls=MyEncoder))
    print("write done")
    """
    return ret_task_graph

def handle_others_output(input_json,computation_ability,num_of_rows,output_file_name):
    task_graph={}
    with open(input_json,'r') as f1:
        task_graph=json.load(f1)

    for i in task_graph.keys():
        mapto=task_graph[i]['mapto']
        task_graph[i]['exe_time']=computation_ability[int(i)][mapto]
    
    with open(output_file_name,"w") as f2:
        f2.write(json.dumps(task_graph,cls=MyEncoder))
    print("write done")


def read_NoC(NoC_file_name):
    ret=[]
    f=open(NoC_file_name)
    for line in f:
        tmp=[]
        for i in line[1:-2].split(','):
            tmp.append(int(i))
        ret.append(tmp)
    return ret


if __name__ == '__main__':

    MapResults={0: 29, 1: 30, 2: 37, 3: 3, 4: 55, 5: 33, 6: 48, 7: 51, 8: 56, 9: 11, 10: 8, 11: 21}
    task_graph={'1': {'out_links': [['2', 190, [[29, 'E']], 0, 0, -1]]}, '2': {'out_links': [['4', 70, [[30, 'W'], [29, 'N'], [21, 'W'], [20, 'W'], [19, 'N'], [11, 'N']], 0, 0, -1], ['5', 140, [[30, 'E'], [31, 'S'], [39, 'S'], [47, 'S']], 0, 0, -1], ['6', 130, [[30, 'S'], [38, 'W'], [37, 'W'], [36, 'W'], [35, 'W'], [34, 'W']], 0, 0, -1], ['7', 70, [[30, 'W'], [29, 'S'], [37, 'S'], [45, 'S'], [53, 'W'], [52, 'W'], [51, 'W'], [50, 'W'], [49, 'W']], 0, 0, -1], ['8', 60, [[30, 'S'], [38, 'S'], [46, 'S'], [54, 'W'], [53, 'W'], [52, 'W']], 0, 0, -1], ['9', 100, [[30, 'S'], [38, 'S'], [46, 'S'], [54, 'S'], [62, 'W'], [61, 'W'], [60, 'W'], [59, 'W'], [58, 'W'], [57, 'W']], 0, 0, -1], ['10', 80, [[30, 'N'], [22, 'N'], [14, 'W'], [13, 'W'], [12, 'W']], 0, 0, -1], ['11', 100, [[30, 'N'], [22, 'N'], [14, 'W'], [13, 'W'], [12, 'W'], [11, 'W'], [10, 'W'], [9, 'W']], 0, 0, -1]]}, '4': {'out_links': [['3', 70, [[3, 'S'], [11, 'S'], [19, 'S'], [27, 'S'], [35, 'E'], [36, 'E']], 0, 0, -1]]}, '5': {'out_links': [['3', 70, [[55, 'N'], [47, 'N'], [39, 'W'], [38, 'W']], 0, 0, -1]]}, '6': {'out_links': [['3', 40, [[33, 'E'], [34, 'E'], [35, 'E'], [36, 'E']], 0, 0, -1]]}, '7': {'out_links': [['3', 90, [[48, 'E'], [49, 'E'], [50, 'E'], [51, 'E'], [52, 'E'], [53, 'N'], [45, 'N']], 0, 0, -1]]}, '8': {'out_links': [['3', 50, [[51, 'N'], [43, 'E'], [44, 'E'], [45, 'N']], 0, 0, -1]]}, '9': {'out_links': [['3', 100, [[56, 'E'], [57, 'N'], [49, 'E'], [50, 'E'], [51, 'E'], [52, 'E'], [53, 'N'], [45, 'N']], 0, 0, -1]]}, '10': {'out_links': [['3', 40, [[11, 'E'], [12, 'E'], [13, 'S'], [21, 'S'], [29, 'S']], 0, 0, -1]]}, '11': {'out_links': [['3', 80, [[8, 'E'], [9, 'S'], [17, 'E'], [18, 'S'], [26, 'E'], [27, 'S'], [35, 'E'], [36, 'E']], 0, 0, -1]]}, '3': {'out_links': [['12', 210, [[37, 'N'], [29, 'N']], 0, 0, -1]]}, '12': {'out_links': []}}

    computation_ability=read_NoC('./NoC Description/N12_autocor_Mesh8x8_NoCdescription.txt')

    dir_name='./gem5_pending_results_'+str(datetime.datetime.now().month)+'.'+str(datetime.datetime.now().day)+'/'

    if(os.path.exists(dir_name)==False):
        os.makedirs(dir_name)

    """
    json_list=[]
    for i in os.listdir('./'):
        if(i[-5:]=='.json'):
            json_list.append(i)
    print("handle json files:")
    print(json_list)
    for i in json_list:
        handle_others_output(i,computation_ability,num_of_rows=8,output_file_name=dir_name+'_test_'+i)
    """


