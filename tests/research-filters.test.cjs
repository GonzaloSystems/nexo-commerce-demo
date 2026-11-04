const test=require('node:test'),assert=require('node:assert/strict'),R=require('../research-filters.js');
const rows=[{asin:'B000000001',title:'Sony Audífonos Bluetooth',price:900,units_30d:null,revenue_30d:null,monthly_units_min:1000,reviews:20},{asin:'B000000002',title:'Sony funda para audífonos',price:0,units_30d:0,revenue_30d:0,monthly_units_min:null,reviews:0},{asin:'B000000003',title:'JBL audífonos bluetooth',price:400,units_30d:300,revenue_30d:120000,monthly_units_min:400,reviews:200}];
test('sales order uses estimates, not public thresholds; unknown stays last',()=>assert.deepEqual([...rows].sort(R.compare('units')).map(p=>p.asin),['B000000003','B000000002','B000000001']));
test('empty sales never pass a numeric limit, and known zero is preserved',()=>{const f=R.parse({unitsMin:'0'});assert.equal(R.matches(rows[0],f),false);assert.equal(R.matches(rows[1],f),true);assert.equal(R.metric(rows[1],'units'),0);});
test('combined keywords support accents, multiple inclusion and exclusion',()=>{const f=R.parse({include:'audifonos, bluetooth',exclude:'funda, repuesto'});assert.equal(R.matches(rows[0],f),true);assert.equal(R.matches(rows[1],f),false);});
test('invalid ranges and identifiers are rejected',()=>{assert.throws(()=>R.parse({priceMin:100,priceMax:50}));assert.throws(()=>R.parse({ids:'not-an-asin'}));});
test('numeric price and revenue sort with missing values after known zeros',()=>assert.deepEqual([{price:null},{price:0},{price:20}].sort(R.compare('price','asc')).map(p=>p.price),[0,20,null]));

test('brand terms separated by commas are alternatives',()=>{const f=R.parse({brand:'Sony, JBL'});assert.equal(R.matches(rows[0],f),true);assert.equal(R.matches(rows[2],f),true);});
