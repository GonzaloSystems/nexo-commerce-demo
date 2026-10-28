"""Time-aligned features; no labels or commercial accuracy are manufactured."""
from datetime import datetime,timedelta,timezone
from math import log,exp
from .normalize import DataError

def dt(value):
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)

def weighted_feature(events,start,end,geometric=False,max_carry_hours=24):
    begin,finish=dt(start),dt(end)
    if finish<=begin or max_carry_hours<=0:raise DataError('invalid_history_window')
    ordered=sorted(events,key=lambda e:e['at'])
    total=(finish-begin).total_seconds();valid_seconds=0;weighted=0
    for i,e in enumerate(ordered):
        at=dt(e['at'])
        next_at=dt(ordered[i+1]['at']) if i+1<len(ordered) else finish
        left=max(at,begin);right=min(next_at,finish,at+timedelta(hours=max_carry_hours))
        seconds=(right-left).total_seconds()
        value=e.get('value')
        if seconds<=0 or value is None or e.get('state')!='observed' or (geometric and value<=0):continue
        valid_seconds+=seconds;weighted+=(log(value) if geometric else value)*seconds
    raw=(exp(weighted/valid_seconds) if geometric else weighted/valid_seconds) if valid_seconds else None
    return {'value':raw,'coverage':valid_seconds/total,'covered_hours':valid_seconds/3600,
            'max_carry_hours':max_carry_hours,'semantics':'piecewise_constant_with_expiry_not_daily_samples'}

def period_features(store,asin,category,start,end,provider='keepa',min_coverage=.9):
    begin=dt(start).replace(hour=0,minute=0,second=0,microsecond=0)
    last=dt(end).replace(hour=0,minute=0,second=0,microsecond=0)
    if (last-begin).days!=29:raise DataError('model_requires_30_inclusive_days')
    finish=last+timedelta(days=1)
    rank=weighted_feature(store.history(asin,'rank',category,provider),begin.isoformat(),finish.isoformat(),True)
    price=weighted_feature(store.history(asin,'price:new_lowest','',provider),begin.isoformat(),finish.isoformat())
    return {'product_id':asin,'country':'MX','marketplace':'amazon','category_id':str(category),
            'period_start':begin.date().isoformat(),'period_end':last.date().isoformat(),
            'bsr_geomean':rank['value'] if rank['coverage']>=min_coverage else None,
            'rank_coverage':rank['coverage'],'price_mean':price['value'] if price['coverage']>=min_coverage else None,
            'price_coverage':price['coverage'],'provider':provider,'minimum_coverage':min_coverage,
            'units_30d':None,'truth_source':None,'training_ready':False,
            'note':'Join independent product-total sales for these exact dates and category; public monthlySold thresholds are not exact sales labels.'}
