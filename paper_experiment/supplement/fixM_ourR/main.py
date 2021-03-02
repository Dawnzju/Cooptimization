import numpy as np
import json
from libs import init,Get_Neighborhood,Get_mapping_exe_time,Get_detailed_data,Get_rand_computation_ability2,CVB_method,read_NoC,init_from_json,Get_weight,MyEncoder
import copy
from routing import improved_routeCompute
import time
import os
from re import findall

json_list=[]
for i in os.listdir('./json_files/'):
    if(i[-5:]=='.json'):
        json_list.append(i)
print("handle json files:",json_list)

NoC_description_dict={'Audiobeam':'N22_audiobeam_Mesh','Autocor':'N12_autocor_Mesh','FMRadio':'N31_fmradio_Mesh','H264':'N51_H264_Mesh'}

degree=['0.25','0.75','1']

f = open("./route_time.txt", 'w+')

for cur_json in json_list:
    str_split=cur_json.split('_')
    num_of_rows=int(findall(r"\d+\.?\d*",str_split[1])[-1])
    air_num=int(findall(r"\d+\.?\d*",str_split[2])[-1])
    for cur_degree in degree:
        adj_matrix,total_needSend,total_needReceive,execution,num_of_tasks=init_from_json('./json_files/'+cur_json)
        computation_ability=[]
        if(air_num==1):
            NoC_description_file=NoC_description_dict[str_split[0]]+str(num_of_rows)+'x'+str(num_of_rows)+'_NoCdescription_V'+cur_degree+'.txt'
            computation_ability=read_NoC('./NoC description/'+NoC_description_file)
        else:
            V_machine=float(cur_degree)
            computation_ability=CVB_method(execution,V_machine,num_of_rows)
            f_noc = open("./ret_NoC_description/"+str_split[0]+"_"+str_split[1]+"_"+str_split[2]+"_V"+cur_degree+".txt", 'w+')
            print("This is computation ability:",file=f_noc)
            print("[",file=f_noc)
            for i in computation_ability:
                print("[",end="",file=f_noc)
                for j in i:
                    print(j,end=",",file=f_noc)
                print("]",file=f_noc)
            print("]",file=f_noc)
            f_noc.close()
        task_graph={}
        with open('./json_files/'+cur_json,'r') as f1:
            task_graph=json.load(f1)
        
        for i in task_graph.keys():
            mapto=task_graph[i]['mapto']
            task_graph[i]['exe_time']=computation_ability[int(i)][mapto]

        map_results=[-1]#把task编号改成从1开始，然后传给routing部分
        for i in range(0,num_of_tasks):
            map_results.append(task_graph[str(i)]['mapto'])
        execution_to_routing=copy.deepcopy(execution)
        for i in range(1,num_of_tasks+1):
            execution_to_routing[i]=computation_ability[i-1][map_results[i]]
        
        start_time=time.time()
        _,route=improved_routeCompute(adj_matrix,num_of_tasks,execution_to_routing,num_of_rows,map_results)
        end_time=time.time()
        
        print(str_split[0]+' '+str(num_of_rows)+'x'+str(num_of_rows)+' V'+cur_degree+' :',end_time-start_time,'seconds',file=f)

        ret_route={}
        for i in route.keys():
            for j in range(len(route[i]['out_links'])):
                route[i]['out_links'][j][0]=int(route[i]['out_links'][j][0])
                route[i]['out_links'][j].insert(2,[])
                route[i]['out_links'][j][3]=[ route[i]['out_links'][j][3] ]
                mapto=map_results[int(i)]
                route[i]['out_links'][j][-2]=mapto
                dest_position=map_results[1:][route[i]['out_links'][j][0]-1]
                route[i]['out_links'][j][-1]=dest_position
                route[i]['out_links'][j]=[ route[i]['out_links'][j] ]
        for i in route.keys():
            cur_key=str(int(i)-1)
            ret_route.update({cur_key:route[i]})
            for j in range(len(ret_route[cur_key]['out_links'])):
                ret_route[cur_key]['out_links'][j][0][0]-=1
        
        for i in task_graph.keys():
            task_graph[i]['out_links']=ret_route[i]['out_links']
        
        #print(task_graph)
        output_file_name=str_split[0]+'_'+str_split[1]+'_'+str_split[2]+'_fixedM_ourR_V'+cur_degree+'.json'
        with open('./outputs_json/'+output_file_name,"w") as f2:
            f2.write(json.dumps(task_graph,cls=MyEncoder))
        print(output_file_name,'done')

f.close()