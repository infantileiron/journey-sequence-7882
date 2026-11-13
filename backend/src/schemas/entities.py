from pydantic import BaseModel,Field,ConfigDict,field_validator
from typing import Literal
class StrictModel(BaseModel):
 model_config=ConfigDict(allow_inf_nan=False)
class LoginInput(StrictModel):
 email:str
 password:str
class DictionaryEntry(StrictModel):
 code:str=Field(pattern=r'^[A-Z][A-Z0-9_]{0,15}$')
 label:str=Field(min_length=1,max_length=30)
class DictionaryInput(StrictModel):
 name:str=Field(min_length=2,max_length=100)
 entries:list[DictionaryEntry]=Field(min_length=2,max_length=8)
class DatasetInput(StrictModel):
 name:str=Field(min_length=2,max_length=100)
 source:str=Field(default='gallery_paths_202611.csv',max_length=100)
 dictionary_id:str='dict-gallery'
 csv_text:str=Field(min_length=20,max_length=1000000)
class RenameDataset(StrictModel):
 name:str=Field(min_length=2,max_length=100)
class SequenceStudyInput(StrictModel):
 name:str=Field(min_length=2,max_length=100)
 dataset_id:str
 min_support:float=Field(default=.1,gt=0,le=1)
 max_length:int=Field(default=3,ge=1,le=4)
 collapse_repeats:bool=True
 insert_cost:int=1
 delete_cost:int=1
 substitute_cost:int=1
 @field_validator('insert_cost','delete_cost','substitute_cost')
 @classmethod
 def positive_cost(cls,value):
  if value<1:raise ValueError('补入、删去、替换成本必须是正整数')
  return value
class RunInput(StrictModel):
 study_id:str
class ReviewInput(StrictModel):
 run_id:str
 comment:str=Field(min_length=5,max_length=2000)
class DecisionInput(StrictModel):
 status:Literal['approved','rejected']
 comment:str=Field(min_length=5,max_length=2000)
class ReportInput(StrictModel):
 run_id:str
 review_id:str
 title:str=Field(min_length=2,max_length=100)
