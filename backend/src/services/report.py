import csv,io
from fastapi import HTTPException
from src.models.entities import Report
from src.config.settings import ARTIFACT_DIR
from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.services.edit_distance import cost_basis,edit_costs

def safe_cell(value):return "'"+value if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')) else value
def list_reports():return repo.all_rows('reports')
def create(data):
 run,review=repo.get('runs',data.run_id),repo.get('reviews',data.review_id)
 if review['status']!='approved' or review['run_id']!=run['id'] or run['status']!='completed':raise ValueError('报告必须引用该运行已通过的复核')
 report=repo.put('reports',Report(new_id('rpt'),data.run_id,data.review_id,data.title,now()));ARTIFACT_DIR.mkdir(parents=True,exist_ok=True);(ARTIFACT_DIR/(report['id']+'.csv')).write_text(download(report['id']),encoding='utf-8');return report
def result_costs(r):
 # Runs completed before cost fields existed are interpreted with unit costs.
 return r.get('edit_costs') or edit_costs(r.get('study')),r.get('cost_basis') or cost_basis(r.get('study'))
def operation_cost(operation,applied):
 return operation.get('cost',0 if operation['operation']=='keep' else applied[operation['operation']])
def download(id):
 report=repo.get('reports',id);run=repo.get('runs',report['run_id']);r=run['result']
 if repo.get('reviews',report['review_id'])['status']!='approved':raise HTTPException(403,'复核未通过')
 applied_costs,basis=result_costs(r)
 out=io.StringIO();w=csv.writer(out)
 w.writerow(['report','journeys','unique_paths','collapse_repeats','total_patterns','patterns_truncated','checksum'])
 w.writerow([safe_cell(report['title']),r['journeys'],r['unique_paths'],r['collapse_repeats'],r['total_patterns'],r['patterns_truncated'],r['checksum']])
 w.writerow([]);w.writerow(['insert_cost','delete_cost','substitute_cost','cost_basis']);w.writerow([applied_costs['insert'],applied_costs['delete'],applied_costs['substitute'],basis])
 w.writerow([]);w.writerow(['pattern','journey_count','support','converted_support','exited_support','support_difference'])
 for p in r['patterns']:w.writerow(['>'.join(p['pattern']),p['count'],p['support'],p['converted_support'],p['exited_support'],p['support_difference']])
 w.writerow([]);w.writerow(['group','medoid','journeys','weighted_total_distance','mean_distance','distance_direction'])
 for group,m in r['medoids'].items():
  if m:w.writerow([group,'>'.join(m['path']),m['journeys'],m['weighted_total_distance'],m['mean_distance'],m.get('distance_direction','actual_to_representative')])
 w.writerow([]);w.writerow(['exited_path','frequency','nearest_converted_path','edit_distance','total_cost','distance_direction','operations'])
 for a in r['alignments']:w.writerow(['>'.join(a['exited_path']),a['frequency'],'>'.join(a['converted_path']),a['distance'],a.get('total_cost',a['distance']),a.get('distance_direction','exited_to_converted'),';'.join(f"{x['operation']}:{x['from'] or '-'}>{x['to'] or '-'}@{operation_cost(x,applied_costs)}" for x in a['operations'])])
 return '\ufeff'+out.getvalue()
