import hashlib,json
from src.services.prefixspan import mine_patterns
from src.services.edit_distance import representatives,cost_basis,edit_costs
from src.constants.domain import MAX_UNIQUE_PATHS

def analyze(rows,dictionary,study):
 normalized=[]
 codes={e['code'] for e in dictionary['entries']}
 for r in rows:
  path=r['path']
  if not path or any(x not in codes for x in path):raise ValueError('空路径或未知触点')
  if study['collapse_repeats']:path=[x for i,x in enumerate(path) if i==0 or path[i-1]!=x]
  normalized.append({**r,'path':path})
 # Bound medoid work before either algorithm starts.
 if len({tuple(r['path']) for r in normalized})>MAX_UNIQUE_PATHS:raise ValueError('唯一序列超过160，请缩小样本或预先分组')
 costs=edit_costs(study);basis=cost_basis(study)
 patterns=mine_patterns(normalized,study['min_support'],study['max_length']);medoids=representatives(normalized,costs)
 return {**patterns,**medoids,'dictionary':dictionary,'study':study,'edit_costs':costs,'cost_basis':basis,'journeys':len(rows),'raw_events':sum(len(r['path']) for r in rows),'normalized_events':sum(len(r['path']) for r in normalized),'collapse_repeats':study['collapse_repeats'],'checksum':hashlib.sha256(json.dumps({'rows':rows,'dictionary':dictionary,'study':study},sort_keys=True).encode()).hexdigest(),'limitations':['频繁子序列允许中间跳过触点，并非连续片段；支持度分母是旅程数，同一旅程每个模式最多计1次','转化/退出组支持差仅描述关联；模拟路径不用于因果或通道归因','补入/删去/替换按方案正整数成本计费，保留成本0；距离方向为实际路径→代表路径，medoid按序列频数加权，平局按编码字典序','最近成功路径按实际退出路径→成功路径的同方向加权距离最近者；对齐平局优先保留、替换、删去、补入，成本合计等于距离','旧方案缺少成本字段时按单位成本1解释，部分缺字段按单位成本补齐；最多2000旅程、每条20触点、160唯一序列、模式长度4、候选6000；结果最多展示200模式与12条退出对齐']}
