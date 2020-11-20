import os
import sys
import getopt
import json

def processorFolder(path):
    fileList = os.listdir(path)
    # outpath = path+"_result"
    # if(os.path.exists(outpath)):
    #     print("outpath exists")
    # else:
    #     os.system("mkdir "+outpath)
    #     print("make dir outpath")
    for file in fileList:
        namelist = file.split('_')
        print(file)
        namelist = namelist[1:]
        print("here",namelist)
        temp = namelist[1].split('x')
        size = temp[1]
        print(size)
        temp = namelist[-1].split('.')
        print(temp)
        type1 = temp[0]
        
        
        inputdir = path +"/" + file
        print(inputdir)

        with open(inputdir) as load_f:
            load_dict = json.load(load_f)
            z = 1
            if(len(namelist)>=5 and namelist[3]!=''):
                for key,value in load_dict.items():
                    for i in range(0,len(load_dict[key]['out_links'])):
                        try:
                            load_dict[key]['out_links'][i][0][3] = load_dict[key]['out_links'][i][0][3][0]
                            load_dict[key]['out_links'][i].remove(load_dict[key]['out_links'][i][-1])
                        except IndexError:
                            z=0


            if(len(namelist)>=5):
                outfile = namelist[0]+"_"+namelist[1]+"_"+namelist[2]+"_"+namelist[3]+namelist[-1]
            else:
                outfile = namelist[0]+"_"+namelist[1]+"_"+namelist[2]+"_"+namelist[-1]
            print(outfile)
            outpath = "./transResult"
            if(os.path.exists(outpath)):
                print("outpath exists")
            else:
                os.system("mkdir "+outpath)
                print("make dir outpath")
            outdir = outpath+"/"+outfile
            with open(outdir,"w") as outfile:
                json.dump(load_dict,outfile)
        #print(outputname)

         
        #os.system('ls')


def main(argv):
    inputfile = ''
    saveflag = 1
    unit = 1
    size = 8
    taskMax = 500

    try:
        opts, args = getopt.getopt(argv,"hi:u:s:",["ifile=","size=","unit="])
    except getopt.GetoptError:
        print('Error run_folder.py -i <inputfile> -s <size> -u <unit>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('run_folder.py -i <folder> -s <size> -u <unit>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            print("read input file")
            inputfile = arg
        elif opt in ("-u", "--unit"):
            unit = int(arg)
        elif opt in ("-s", "--size"):
            size = int(arg)
        # elif opt in ("-u", "--unit"):
        #     unit = int(arg)


    print('inputfile: ', inputfile)
    print('saveflag: ', saveflag)
    print('unit: ',unit)
    print('size: ',size)
    processorFolder(inputfile)


if __name__ == "__main__":
    main(sys.argv[1:])