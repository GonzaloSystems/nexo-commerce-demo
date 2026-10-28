from datetime import datetime, timezone, timedelta
from math import isfinite
from .providers import ASIN_RE, MARKETPLACE_MX

KEEPA_EPOCH = datetime(2011,1,1,tzinfo=timezone.utc)

class DataError(Exception):
    pass

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def number(v):
    if isinstance(v,bool): return None
    try:
        n=float(v)
        return n if isfinite(n) else None
    except (ValueError,TypeError): return None

def keepa_time(v, zero_unknown=False):
    n=number(v)
    if n is None or n<0 or (zero_unknown and n==0): return None
    try:return (KEEPA_EPOCH+timedelta(minutes=n)).isoformat(timespec='seconds')
    except (OverflowError,ValueError):return None

def pairs(values, money=False):
    if values is None:return []
    if not isinstance(values,list) or len(values)%2:raise DataError('invalid_history_pairs')
    result={}
    for i in range(0,len(values),2):
        stamp=keepa_time(values[i]);v=number(values[i+1])
        if stamp is None or v is None:raise DataError('invalid_history_value')
        # Negative values are provider sentinels, never zero price/rank/sales.
        result[stamp]={'at':stamp,'value':v/100 if money and v>=0 else v if v>=0 else None,
                       'state':'observed' if v>=0 else 'unavailable_or_unknown','provider_value':values[i+1]}
    return [result[k] for k in sorted(result)]

def latest(series):
    return series[-1] if series else {'at':None,'value':None,'state':'missing'}

def base_record(asin, provider, queried_at):
    if not isinstance(asin,str) or not ASIN_RE.fullmatch(asin):raise DataError('invalid_asin')
    return {'schema_version':1,'asin':asin,'parent_asin':None,'child_asins':[], 'variations':[],
            'marketplace':'amazon','country':'MX','marketplace_id':MARKETPLACE_MX,'currency':'MXN',
            'provider':provider,'queried_at':queried_at,'provider_updated_at':None,
            'title':None,'brand':None,'color':None,'image_url':None,'category_tree':[],
            'rank_current':None,'rank_category_id':None,'rank_category_name':None,'rank_observed_at':None,
            'price_current':None,'price_kind':None,'price_observed_at':None,'availability':'unknown',
            'new_offer_count':None,'offer_count_total':None,'seller_count_observed':None,'seller_count_scope':None,
            'monthly_units_min':None,'monthly_units_scope':None,'monthly_units_observed_at':None,
            'actual_competitor_sales':None,'actual_competitor_revenue':None,
            'rank_history_by_category':{},'price_history':{},'offer_count_history':[],
            'monthly_units_min_history':[], 'quality_warnings':[]}

def keepa_product(p, queried_at=None):
    if p.get('domainId')!=11:raise DataError('wrong_keepa_marketplace')
    r=base_record(p.get('asin'),'keepa',queried_at or utc_now())
    for key in ('title','brand','color'):
        if isinstance(p.get(key),str):r[key]=p[key][:2000]
    parent=p.get('parentAsin')
    if isinstance(parent,str) and ASIN_RE.fullmatch(parent):r['parent_asin']=parent
    variations=p.get('variations') or []
    for v in variations:
        if isinstance(v,dict) and isinstance(v.get('asin'),str) and ASIN_RE.fullmatch(v['asin']):
            r['variations'].append({'asin':v['asin'],'attributes':v.get('attributes') or []})
    # Keepa's variation list may contain siblings, not just children of this ASIN.
    if r['parent_asin']==r['asin']:
        r['child_asins']=[v['asin'] for v in r['variations'] if v['asin']!=r['asin']]
    tree=p.get('categoryTree') or []
    r['category_tree']=[{'id':str(c['catId']),'name':str(c.get('name',''))} for c in tree if isinstance(c,dict) and c.get('catId') not in (None,0,9223372036854775807)]
    ref=p.get('salesRankReference')
    if ref not in (None,0,-1,9223372036854775807):r['rank_category_id']=str(ref)
    r['rank_category_name']=next((c['name'] for c in r['category_tree'] if c['id']==r['rank_category_id']),None)
    r['provider_updated_at']=keepa_time(p.get('lastUpdate'),True)
    r['offers_updated_at']=keepa_time(p.get('lastOffersUpdate'),True)
    r['stock_updated_at']=keepa_time(p.get('lastStockUpdate'),True)
    images=p.get('images') or []
    for im in images:
        if not isinstance(im,dict):continue
        filename=im.get('l') or im.get('m')
        if isinstance(filename,str) and all(c.isalnum() or c in '._+-' for c in filename):
            r['image_url']='https://m.media-amazon.com/images/I/'+filename
            break
    csv=p.get('csv') or []
    def series_at(i,money=False):
        try:return pairs(csv[i] if i<len(csv) else None,money)
        except (DataError,TypeError):r['quality_warnings'].append(f'invalid_csv_series:{i}');return []
    for name,i in [('amazon',0),('new_lowest',1)]:r['price_history'][name]=series_at(i,True)
    def decode(values,label):
        try:return pairs(values)
        except DataError:r['quality_warnings'].append('invalid_history:'+label);return []
    for cat,values in (p.get('salesRanks') or {}).items():r['rank_history_by_category'][str(cat)]=decode(values,str(cat))
    ref_history=p.get('salesRankReferenceHistory') or []
    if r['rank_category_id'] and r['rank_category_id'] not in r['rank_history_by_category']:
        # csv[3] can switch category references over time. Preserve current rank,
        # but do not treat it as a stable-category history after such a switch.
        raw=series_at(3)
        if ref_history:
            r['quality_warnings'].append('rank_reference_changed_csv3_not_used_for_history')
        else:r['rank_history_by_category'][r['rank_category_id']]=raw
    rank_series=r['rank_history_by_category'].get(r['rank_category_id'],[])
    rank=latest(rank_series or series_at(3))
    if rank['value'] is not None and rank['value']>0:
        r['rank_current']=int(rank['value']);r['rank_observed_at']=rank['at']
    current=(p.get('stats') or {}).get('current') or []
    def current_at(i):
        n=number(current[i]) if i<len(current) else None
        return n if n is not None and n>=0 else None
    # Use an explicitly named price basis, not an unlabeled mix of Amazon,
    # lowest new offer and Buy Box. All values are MXN centavos for domain 11.
    for name,i in [('new_lowest',1),('amazon',0)]:
        h=latest(r['price_history'][name]);n=current_at(i)
        price=(n/100 if n is not None else None) if i<len(current) and number(current[i]) is not None else h['value']
        if price is not None:
            r['price_current']=price;r['price_kind']=name;r['price_observed_at']=r['provider_updated_at'] if n is not None else h['at']
            r['availability']='price_offer_observed';break
    r['offer_count_history']=series_at(11)
    count=current_at(11)
    if count is None and not (11<len(current) and number(current[11]) is not None):count=latest(r['offer_count_history'])['value']
    if count is not None:
        r['new_offer_count']=int(count);r['seller_count_observed']=int(count)
        r['seller_count_scope']='keepa_count_new_merchants_snapshot_not_inventory'
    sold=number(p.get('monthlySold'))
    if sold is not None and sold>0:
        r['monthly_units_min']=int(sold);r['monthly_units_scope']='public_bought_past_month_threshold_variation_specific'
        r['monthly_units_observed_at']=keepa_time(p.get('lastSoldUpdate'),True)
    r['monthly_units_min_history']=decode(p.get('monthlySoldHistory'),'monthlySoldHistory')
    r['quality_warnings'].append('signals_are_not_ground_truth_competitor_sales')
    return r

def sp_product(bundle, queried_at=None):
    p=bundle.get('catalog') or {}
    r=base_record(p.get('asin'),'sp-api',queried_at or utc_now())
    summaries=[s for s in p.get('summaries',[]) if s.get('marketplaceId')==MARKETPLACE_MX]
    if summaries:
        s=summaries[0];r.update(title=s.get('itemName'),brand=s.get('brand'),color=s.get('color'))
        c=s.get('browseClassification') or {}
        if c.get('classificationId'):r['category_tree']=[{'id':str(c['classificationId']),'name':c.get('displayName','')}]
    for group in p.get('classifications',[]):
        if group.get('marketplaceId')==MARKETPLACE_MX:
            for c in group.get('classifications',[]):
                if c.get('classificationId'):r['category_tree'].append({'id':str(c['classificationId']),'name':c.get('displayName','')})
    for group in p.get('images',[]):
        if group.get('marketplaceId')==MARKETPLACE_MX:
            images=group.get('images') or []
            if images:r['image_url']=images[0].get('link')
    for group in p.get('relationships',[]):
        if group.get('marketplaceId')!=MARKETPLACE_MX:continue
        for rel in group.get('relationships',[]):
            if rel.get('type')!='VARIATION':continue
            parents=rel.get('parentAsins') or []
            if parents:r['parent_asin']=parents[0]
            r['child_asins'].extend(rel.get('childAsins') or [])
    r['variations']=[{'asin':a,'attributes':[]} for a in r['child_asins']]
    for group in p.get('salesRanks',[]):
        if group.get('marketplaceId')!=MARKETPLACE_MX:continue
        # Keep classification ranks separate from display-group identifiers.
        for rank in group.get('classificationRanks',[]):
            n=number(rank.get('rank'));cat=rank.get('classificationId')
            if n is not None and n>0 and cat:
                ev={'at':r['queried_at'],'value':int(n),'state':'observed','provider_value':int(n)}
                r['rank_history_by_category'][str(cat)]=[ev]
                if r['rank_current'] is None:
                    r['rank_current']=int(n);r['rank_category_id']=str(cat);r['rank_category_name']=rank.get('title');r['rank_observed_at']=r['queried_at']
        r['display_group_ranks']=group.get('displayGroupRanks') or []
    payload=((bundle.get('offers') or {}).get('payload') or {})
    if payload and payload.get('ASIN') not in (None,r['asin']):raise DataError('offers_asin_mismatch')
    if payload and payload.get('marketplaceId') not in (None,MARKETPLACE_MX):raise DataError('offers_marketplace_mismatch')
    summary=payload.get('Summary') or {}
    for kind,field in [('buy_box','BuyBoxPrices'),('new_lowest','LowestPrices')]:
        for price in summary.get(field,[]):
            if str(price.get('condition','New')).lower()!='new':continue
            money=price.get('LandedPrice') or price.get('ListingPrice') or {}
            n=number(money.get('Amount'))
            if money.get('CurrencyCode')=='MXN' and n is not None and n>=0:
                r['price_current']=n;r['price_kind']=kind;r['price_observed_at']=r['queried_at'];break
        if r['price_current'] is not None:break
    count=number(summary.get('TotalOfferCount'))
    if count is not None and count>=0:r['offer_count_total']=int(count)
    new_counts=[number(o.get('OfferCount')) for o in summary.get('NumberOfOffers',[]) if str(o.get('condition','')).lower()=='new']
    if new_counts and all(n is not None and n>=0 for n in new_counts):r['new_offer_count']=int(sum(new_counts))
    offers=payload.get('Offers') or []
    sellers={o['SellerId'] for o in offers if o.get('SellerId')}
    if sellers:
        r['seller_count_observed']=len(sellers);r['seller_count_scope']='distinct_sellers_in_returned_offers_not_total_market'
    if r['price_current'] is not None:r['availability']='price_offer_observed'
    r['pricing_status']=bundle.get('pricing_status','unknown')
    r['quality_warnings']=['sp_api_has_no_backfilled_rank_or_price_history','offer_count_is_not_exact_unique_seller_count','signals_are_not_ground_truth_competitor_sales']
    return r
