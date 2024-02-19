_B=False
_A=None
from models import User,SubmitRecord,FileUpload,ChunkedFile
from app import db,log
import requests,os,shutil
def get_user(query):
        B=query
        try:
                A=User.query.filter_by(**B).first()
                if A is _A:A=User(**B);db.session.add(A);db.session.commit();log.info(f"Inserted user to db");A=User.query.filter_by(**B).first()
                return A
        except Exception as C:print(f"Error occurred in get_user: {str(C)}");return    
def get_submit_record(query):
        B=query
        try:
                A=SubmitRecord.query.filter_by(**B).first()
                if A is _A:A=SubmitRecord(**B);db.session.add(A);db.session.commit();log.info(f"Inserted submit record to db");A=SubmitRecord.query.filter_by(**B).first()    
                return A
        except Exception as C:print(f"Error occurred in get_submit_record: {str(C)}");return
def get_file_upload(query,new=_B):
        B=query
        try:
                A=FileUpload.query.filter_by(**B).first()
                if A is _A or new:A=FileUpload(**B);db.session.add(A);db.session.commit();log.info(f"Inserted file upload to db");A=FileUpload.query.filter_by(**B).first()   
                return A
        except Exception as C:print(f"Error occurred in get_file_upload: {str(C)}");return
def is_first_chunk(dzuuid):A=ChunkedFile.query.filter_by(dzuuid=dzuuid).first();return A is _A
def add_chunked_file(**B):
        try:A=ChunkedFile(**B);db.session.add(A);db.session.commit();log.info(f"Inserted chunked file to db");return A
        except Exception as C:print(f"Error occurred in add_chunked_file: {str(C)}");return
def file_exist_check(*A):
        B=os.path.join(*A)
        try:
                with open(B,'r'):return True
        except:return _B
"\nErrors related to file writes should be handled in the main app (centrally)\n  - since user input is involved, it's better to handle it in the main app\nDatabase errors should be handled independently by each helper function\n  - db errors => server problems, only the engineer could fix it (user !involved)\n"
def save_chunk(chunk_content,chunk_path):
        B=chunk_path;A=chunk_content
        if A is _A:raise ValueError('Chunk content is empty')
        with open(B,'wb')as C:C.write(A.read());log.info(f"Saved chunk to {B}")        
def reassemble_file(submit_dir,filename,dztotalchunkcount):
        D=submit_dir;A=filename;B=os.path.join(D,A);E=os.path.join(D,'temp')
        def H():shutil.rmtree(E)
        with open(B,'wb')as I:
                for F in range(dztotalchunkcount):
                        J=os.path.splitext(A)[0];C=f"{J}_{F}.part";G=os.path.join(E,C) 
                        if not os.path.exists(G):raise FileNotFoundError(f"Missing {C} at index {F}")
                        with open(G,'rb')as K:I.write(K.read());log.info(f"Successfully reassembled {C} to {B}")
        if not file_exist_check(B):raise Exception(f"Oops! Critical error occurred while reassembling {A}!")
        H();return True
def upload_smallfile_to_onedrive(local_submit_dir,file_name,msgraph_access_token):     
        R='MediaMod';Q='mediamod@gemadept.com.vn';P='displayName';O='email';N='user';M='01E26M3MJECFCQ4WA5TFBYWDHJGYRPLDH4';L='name';K='lastModifiedDateTime';J='createdDateTime';C='fee2b48b-f942-40a7-9e8a-54d78dbd8397';B='2024-02-07T02:41:10Z';A='id';D='https://graph.microsoft.com/v1.0';E=msgraph_access_token;print('access_token',E);F={'Authorization':f"Bearer {E}",'Content-Type':'application/json'};X={J:B,'eTag':'"{0E451124-1D58-4399-8B0C-E93622F58CFC},1"',A:M,K:B,L:'GMD Thi Ảnh Đẹp 2024','webUrl':'https://gmdcorp-my.sharepoint.com/personal/mediamod_gemadept_com_vn/Documents/GMD%20Thi%20%E1%BA%A2nh%20%C4%90%E1%BA%B9p%202024','cTag':'"c:{0E451124-1D58-4399-8B0C-E93622F58CFC},0"','size':0,'createdBy':{N:{O:Q,A:C,P:R}},'lastModifiedBy':{N:{O:Q,A:C,P:R}},'parentReference':{'driveType':'business','driveId':'b!BSMpwLx6u0q_b-Nt-1W-O7tis30oT8lEvvD4tylYPZ1oPotOMoVXT5wqC5MaOvrI',A:'01E26M3MN6Y2GOVW7725BZO354PWSELRRZ',L:'Documents','path':'/drive/root:','siteId':'c0292305-7abc-4abb-bf6f-e36dfb55be3b'},'fileSystemInfo':{J:B,K:B},'folder':{'childCount':0}},;G=M;H=C;S=f"{D}/users/{H}/drive/items/{G}";T=local_submit_dir;U=requests.get(S,headers=F);print('res, get all drive items',U.json())
        with open(T,'rb')as V:W=V.read()
        I=requests.put(f"{D}/users/{H}/drive/items/{G}:/{file_name}:/content",headers=F,data=W);print('uploading to onedrive',I.json())
        if I.status_code==200:return True
        else:return _B
'\nTwo flows for onedrive upload:\n- Normal file upload (for files < 250MB) according to the ref: https://learn.microsoft.com/en-us/graph/api/driveitem-put-content?view=graph-rest-1.0&tabs=http\n- Large file upload (for files >= 250MB to 500MB in this app)\n'  
def upload_to_onedrive(file_size,filepath,access_token):0
'Recommendation:\n- Implement retry mechanism to handle large file upload\n'
'rety mechanism example\nmax_retries = 3\n    retry_count = 0\n    while retry_count < max_retries:\n      response = requests.put(\n        f"{GRAPH_API_ENDPOINT}/users/{user_id}/drive/items/root:/{file_name}:/content",\n        headers=headers,\n        data=media_content,\n      )\n      if response.status_code == 200:\n        print(response.json())\n        break\n      else:\n        retry_count += 1\n        print(f"Request failed. Retrying... (Attempt {retry_count}/{max_retries})")\n    else:\n      print("Max retries exceeded. Request failed.")\n'