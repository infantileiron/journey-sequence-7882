from collections import Counter
from src.constants.domain import MAX_UNIQUE_PATHS

UNIT_EDIT_COSTS={'insert':1,'delete':1,'substitute':1}
STUDY_COST_FIELDS={'insert':'insert_cost','delete':'delete_cost','substitute':'substitute_cost'}
COST_LABELS={'insert':'补入','delete':'删去','substitute':'替换'}

def positive_int(value,label):
 if isinstance(value,bool) or not isinstance(value,int) or value<1:
  if isinstance(value,float) and value.is_integer():value=int(value)
  else:raise ValueError(f'{label}成本必须是正整数')
 return value

def edit_costs(study=None,costs=None):
 """Resolve positive integer insert/delete/substitute costs; missing fields default to unit cost."""
 values=dict(UNIT_EDIT_COSTS)
 study=study or {}
 if study:
  # Studies saved before cost fields existed fall back per missing field to unit cost.
  values.update({key:positive_int(study[field],COST_LABELS[key]) for key,field in STUDY_COST_FIELDS.items() if field in study})
 if costs:
  if not isinstance(costs,dict):raise ValueError('编辑成本需要补入/删去/替换三个正整数')
  values.update({key:positive_int(costs[key],COST_LABELS[key]) for key in values if key in costs})
 if any(value<1 for value in values.values()):raise ValueError('补入、删去、替换成本必须是正整数')
 return values

def cost_basis(study):
 explicit=sum(field in (study or {}) for field in STUDY_COST_FIELDS.values())
 return 'study' if explicit==3 else 'mixed_study_unit_default' if explicit else 'unit_cost_default'

def levenshtein(a,b,costs=None):
 """Directed distance: transform a (actual path) into b (target path)."""
 costs=costs or UNIT_EDIT_COSTS
 ci,cd,cs=costs['insert'],costs['delete'],costs['substitute']
 previous=[j*ci for j in range(len(b)+1)]
 for i,x in enumerate(a,1):
  current=[i*cd]
  for j,y in enumerate(b,1):current.append(min(previous[j]+cd,current[j-1]+ci,previous[j-1]+(0 if x==y else cs)))
  previous=current
 return previous[-1]

def align(a,b,costs=None):
 """Align a (actual path) onto b (target path); operation costs sum to the distance."""
 costs=costs or UNIT_EDIT_COSTS
 ci,cd,cs=costs['insert'],costs['delete'],costs['substitute']
 d=[[0]*(len(b)+1) for _ in range(len(a)+1)]
 for i in range(len(a)+1):d[i][0]=i*cd
 for j in range(len(b)+1):d[0][j]=j*ci
 for i in range(1,len(a)+1):
  for j in range(1,len(b)+1):
   d[i][j]=min(d[i-1][j]+cd,d[i][j-1]+ci,d[i-1][j-1]+(0 if a[i-1]==b[j-1] else cs))
 i,j=len(a),len(b);operations=[]
 while i or j:
  if i and j and a[i-1]==b[j-1] and d[i][j]==d[i-1][j-1]:operations.append({'operation':'keep','from':a[i-1],'to':b[j-1],'cost':0});i-=1;j-=1
  elif i and j and d[i][j]==d[i-1][j-1]+cs:operations.append({'operation':'substitute','from':a[i-1],'to':b[j-1],'cost':cs});i-=1;j-=1
  elif i and d[i][j]==d[i-1][j]+cd:operations.append({'operation':'delete','from':a[i-1],'to':None,'cost':cd});i-=1
  else:operations.append({'operation':'insert','from':None,'to':b[j-1],'cost':ci});j-=1
 operations.reverse()
 total_cost=sum(o['cost'] for o in operations)
 if total_cost!=d[-1][-1]:raise RuntimeError('对齐成本合计与距离不一致')
 return {'distance':d[-1][-1],'total_cost':total_cost,'costs':costs,'operations':operations}

def representatives(rows,costs=None):
 costs=costs or UNIT_EDIT_COSTS
 groups={'all':Counter(tuple(r['path']) for r in rows),'converted':Counter(tuple(r['path']) for r in rows if r['outcome']=='converted'),'exited':Counter(tuple(r['path']) for r in rows if r['outcome']=='exited')}
 if len(groups['all'])>MAX_UNIQUE_PATHS:raise ValueError('折叠后唯一序列超过160，请缩小样本或预先分组')
 cache={};symmetric=costs['insert']==costs['delete']
 def distance(a,b):
  if a==b:return 0
  # Direction matters only when insert and delete costs differ; keep the pair cache symmetric otherwise.
  key=tuple(sorted((a,b))) if symmetric else (a,b)
  if key not in cache:cache[key]=levenshtein(*key) if symmetric else levenshtein(a,b,costs)
  return cache[key]
 medoids={}
 for group,counts in groups.items():
  if not counts:medoids[group]=None;continue
  # Each actual path is measured toward the candidate representative; ties keep code order.
  cost,path=min((sum(freq*distance(other,path) for other,freq in counts.items()),path) for path in sorted(counts))
  medoids[group]={'path':list(path),'frequency':counts[path],'weighted_total_distance':cost,'mean_distance':cost/sum(counts.values()),'journeys':sum(counts.values()),'distance_direction':'actual_to_representative'}
 alignments=[]
 if groups['converted']:
  for path,freq in sorted(groups['exited'].items(),key=lambda x:(-x[1],x[0]))[:12]:
   # Same actual-to-target direction: exited path onto nearest successful path.
   target=min(groups['converted'],key=lambda p:(distance(path,p),-groups['converted'][p],p))
   alignments.append({'exited_path':list(path),'frequency':freq,'converted_path':list(target),**align(path,target,costs),'distance_direction':'exited_to_converted'})
 return {'medoids':medoids,'alignments':alignments,'unique_paths':len(groups['all']),'distance_cache_pairs':len(cache),'alignment_limit':12,'edit_costs':costs}
