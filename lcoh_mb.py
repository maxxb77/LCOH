
import pandas as pd
import numpy as np
import os
from itertools import product

root_dir = "/Users/max/Documents/GitHub"

cf_char = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","char_cf.csv"))
fuel_prices_state = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","fuel_prices_state.csv"))
state_name_abb = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","state_name_abb.csv"))
state_name_abb['state_name'] = state_name_abb['state_name'].str.lower().str.replace(' ', '')
state_name_abb['state_abb'] = state_name_abb['state_abb'].str.lower().str.replace(' ', '')

def format_columns(df):
    df2 = df
    df2.columns = df.columns.str.replace(' ', '_')
    return df2

cf_char = format_columns(cf_char).fillna(0)

#second row of cf_char contains units, remove it
cf_char = cf_char[cf_char['HYD']!='fraction [rate]']

h2_char = cf_char.copy()
h2_char['HYD'] = h2_char['HYD'].astype(float)
h2_char = h2_char[h2_char['HYD']>0]
h2_char = h2_char[h2_char['id']=='new']


print(cf_char.columns)
remove_columns_h2 = ["id","r","lat","lon","int_elec_self", "int_h2", "int_h2_mark", "int_h2_self", "int_co2", "int_co2_mark", 
                     "int_co2_self", "ee", "cod_dec", "cap_dec", "outage_rate", "min_cap", "int_met_coal_feed", "int_ddfo", 
                     "co2_rate_comb", "co2_rate_proc", "GAS", "JFL", "DDFO", "ETH", "HYD", "COKE" ]


h2_char = h2_char.drop(remove_columns_h2,axis=1)

h2_char_orig = h2_char.copy()

#now need to take those values and re-produce lcoh cases by state
state_h2_char = pd.DataFrame()

#gas prices in $/mwh
'''
gas_low = 0
gas_high = 20
gas_seq = 2
gas_prices = list(range(gas_low, gas_high, gas_seq))

#ele prices in $/mwh
ele_low = 0
ele_high = 100
ele_seq = 5
ele_prices = list(range(ele_low,ele_high,ele_seq))
'''


gas_low = 0
gas_high = 11
gas_seq = 2
gas_prices = list(range(gas_low, gas_high, gas_seq))

#ele prices in $/mwh
ele_low = 0
ele_high = 101
ele_seq = 10
ele_prices = list(range(ele_low,ele_high,ele_seq))

#pounds per mwh
#from: 
co2_ppm = 805 
#convert to tones per mwh
co2_mpm = int((round(co2_ppm / 2200, 5) * 1e3))
co2_mpm_low = 0
co2_step = 100
co2_mpm_high = 2 * co2_mpm

co2_ele = list(range(co2_mpm_low,co2_mpm_high,co2_step))
#@@
#co2_ele = [co2_mpm]

#from: https://stackoverflow.com/questions/25634489/get-all-combinations-of-elements-from-two-lists
#pd.DataFrame(list(product(l1, l2)), columns=['l1', 'l2'])
# no longer used
co2_ng = [0.053, 0.064, 0.075, 0.082, 0.086, 0.111, 0.140]
co2_tax = [0]
co2_tns = [5,15,25]

fuel_comb = pd.DataFrame(list(product(gas_prices, ele_prices, co2_ele, co2_ng, co2_tax, co2_tns)), columns=['gas_price', 'ele_price','co2_ele','co2_ng', 'co2_tax', 'co2_tns'])

#ugly but it works...
#https://stackoverflow.com/questions/16476924/how-can-i-iterate-over-rows-in-a-pandas-dataframe
#call up lionel richie caused we're getting a perm
h2_perm = pd.DataFrame()
# loop over all the rows in the fuel combinations and assign gas/ele prices
for index, row in fuel_comb.iterrows():
    temp = h2_char.copy()
#    for i in row.columns:
#        temp[i] = row[i]
    temp['gas_price'] = row['gas_price']
    temp['ele_price'] = row['ele_price']
    temp['co2_ele'] = row['co2_ele'] / 1e3
    temp['co2_ng'] = row['co2_ng']
    temp['co2_tax'] = row['co2_tax']
    temp['co2_tns'] = row['co2_tns']
    
    h2_perm = pd.concat([h2_perm,temp])
    
'''
[LCOF, Capital  [$/MMBtu]]] = 
[Cost, Cap, Overnight [$/(MMBtu/yr)]]]*[Constr, Depr, Tax Factor]*[CRF]/[Capacity Factor]
# [Constr, Depr, Tax Factor] = 1.17

[LCOF, VOM, Other [$/MMBtu]]] = 
[Cost, VOM (excl. energy & feed) [$/MMBtu]]]

[LCOF, CO2 Emit/Capt [$/MMBtu]]] = 
[Emis, CO2, Total [tonnes/MMBtu]]]*[Price, CO2 Emit/Capt [$/tonne]]]

[LCOF, CO2 Feed [$/MMBtu]]] =
[Int C02 Feed [tonnes/MMBtu]]]*[Price, CO2 Feed [$/tonne]]]

[LCOF, CO2 T&S [$/MMBtu]]] =
[Emis, CO2, Captured [tonnes/MMBtu]]]*[Price, CO2 T&S [$/tonne]]]

[LCOF, Energy, Bio [$/MMBtu]]] =
[Int Bio Feed [dry tonnes/MMBtu]]]*[Price, Biomass Feed [$/dry tonne]]]

[LCOF, Energy, Non-bio [$/MMBtu]]] =
    [Int Ddfo]*[Price, DDFO [$/MMBtu]]]+
    [Int Elec [MWh/MMBtu]]]*[Price, Elec [$/MWh]]]+
    [Int H2 [lbs/MMBtu]]]/2.20462*[Price, H2 [$/kg]]]+
    [Int Met Coal Feed]*[Price, Met. Coal [$/MMBtu]]]+
    [Int NG [MMBtu/MMBtu]]]*[Price, NG [$/MMBtu]]]

[LCOF, FOM [$/MMBtu]]] =
    [Cost, FOM [$/(MMBtu/yr*yr)]]]/[Capacity Factor]

[LCOF, Taxes, Marketing, Distribution [$/MMBtu]]] =
    [Fuel Taxes, Marketing, Distribution [$/MMbtu]]]

'''
  
cdt_factor = 1.17
cap_factor = 0.85
equity_share = 0.4
int_debt = 0.05
tax_rate = 0.25
rroe_real = 0.08
fac_lifetime = 30
inflate = 1.057
emit_coal = 0.094
emit_ddfo = 0.074
emit_ng = 0.053

#compute the WACC and capital recovery factor to use in LCOF
h2_perm['wacc'] = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real
wacc_par = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real

h2_perm['crf'] = (h2_perm['wacc'] * (1+h2_perm['wacc'])**fac_lifetime) / ( (1+h2_perm['wacc'])**fac_lifetime-1 )
crf_par = (wacc_par * (1+wacc_par)**fac_lifetime) / ( (1+wacc_par)**fac_lifetime-1 )

h2_perm['cost_cap'] = h2_perm['cost_cap'].astype(float)
h2_perm['LCOF_cap'] =  h2_perm['cost_cap']/114.877/365*cdt_factor*h2_perm['crf']/cap_factor
h2_perm['LCOF_vom'] = h2_perm['cost_vom'].astype(float)

#!!! if copying this line, need to include other components
h2_perm['emit_rate_comb'] = h2_perm['co2_ng'] * h2_perm['int_ng'].astype(float)
h2_perm['emit_ele'] = h2_perm['co2_ele'] * h2_perm['int_elec'].astype(float)
h2_perm['emit_rate_total'] = h2_perm['emit_rate_comb'] + h2_perm['emit_ele']
#captured emissions do not include upstream accounting
h2_perm['emit_captured'] = h2_perm['ccs_cap_rate_comb'].astype(float) * 0.053 * h2_perm['int_ng'].astype(float)


h2_perm['LCOF_co2_tax_cost'] = h2_perm['co2_tax'] * h2_perm['emit_rate_total']
h2_perm['LCOF_co2_tns'] = h2_perm['co2_tns'] * h2_perm['emit_captured']

#!!!! will also need expanding when looking at steel
h2_perm['LCOF_energy_gas'] = h2_perm['int_ng'].astype(float) * h2_perm['gas_price']
h2_perm['LCOF_energy_elec'] = h2_perm['int_elec'].astype(float) * h2_perm['ele_price'] 

h2_perm['LCOF_fom'] = h2_perm['cost_fom_per_metric_ton'].astype(float)/114.877


components = ['LCOF_cap', 'LCOF_vom', 'LCOF_fom', 'LCOF_co2_tax_cost', 'LCOF_co2_tns','LCOF_energy_gas','LCOF_energy_elec']

# find columns that aren't in components for the melt function
id_vars1 = [x for x in list(h2_perm.columns) if x not in components]

h2_out = pd.melt(h2_perm,value_name='LCOF_Cost',value_vars=components,id_vars = id_vars1)

h2_out.to_csv(os.path.join(root_dir,"LCOH",'h2_perm.csv'))


# ------ begin lcoh by state plot ------- #

fuel_prices_state = fuel_prices_state.drop(['Region'],axis=1)
h2_state = h2_char_orig.merge(fuel_prices_state, how='cross')


#compute the WACC and capital recovery factor to use in LCOF
h2_state['wacc'] = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real
#wacc_par = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real

h2_state['crf'] = (h2_state['wacc'] * (1+h2_state['wacc'])**fac_lifetime) / ( (1+h2_state['wacc'])**fac_lifetime-1 )
#crf_par = (wacc_par * (1+wacc_par)**fac_lifetime) / ( (1+wacc_par)**fac_lifetime-1 )

h2_state['cost_cap'] = h2_state['cost_cap'].astype(float)
h2_state['LCOF_cap'] = h2_state['cost_cap']/114.877/365*cdt_factor*h2_state['crf']/cap_factor
h2_state['LCOF_vom'] = h2_state['cost_vom'].astype(float)

h2_state['emit_captured'] = h2_state['ccs_cap_rate_comb'].astype(float) * 0.053 * h2_state['int_ng'].astype(float)


#h2_state['LCOF_co2_tax_cost'] = h2_state['co2_tax'] * h2_state['emit_rate_total']
h2_state['LCOF_co2_tns'] = h2_state['CCS2'].astype(float) * h2_state['emit_captured']

#!!!! will also need expanding when looking at steel
h2_state['LCOF_energy_gas'] = h2_state['int_ng'].astype(float) * h2_state['Gas']
# note conversion from cents per kwh to dollars per mwh via the factor of 10
h2_state['LCOF_energy_elec'] = 10 * h2_state['int_elec'].astype(float) * h2_state['ELE_IND'] 

h2_state['LCOF_fom'] = h2_state['cost_fom_per_metric_ton'].astype(float)/114.877


components_state = ['LCOF_cap', 'LCOF_vom', 'LCOF_fom', 'LCOF_co2_tns','LCOF_energy_gas','LCOF_energy_elec']

# find columns that aren't in components for the melt function
id_vars2 = [x for x in list(h2_state.columns) if x not in components_state]

h2_state_out = pd.melt(h2_state,value_name='LCOF_Cost',value_vars=components_state,id_vars = id_vars2)

h2_state_out.to_csv(os.path.join(root_dir,"LCOH","lcoh_state.csv"))




#--- begin h2 by county ---#

c2z_loc = "/Users/max/Documents/GitHub/LCOH/raw_data/county2zone.csv"

c2z = pd.read_csv(c2z_loc,names=['fips','ba','county_name','state_abb'],header=0, dtype={'fips': str})

slope_cols = ["county_name","state_full", "state_code", "ele_tech", "year", "gid", "lcoe_min", "lcoe_max", "lcoe_med", "cap_min", "cap_max", "cap_med", "fips"]
lcoe_county = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","SLOPE_LCOE.csv"),names=slope_cols,header=0, dtype={'fips': str})

#updated version - now 2024
#!!!! important assumption here, can choose from any of the values below
#!!!! default/reference is LCOE_min
chosen_lcoe_input = "der_mean"
lcoe_year = 2030
slope_cols_new = ["county_name","state_full", "state_code", "ele_tech","year", "gid", "lcoe_mean", "lcoe_min", "lcoe_max", "lcoe_med", "sd_a", "sd_b", "sd_c","der_mean"]
lcoe_county_new = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","slope_2024.csv"),names=slope_cols_new,header=0, dtype={'fips': str})
lcoe_county_new['fips'] = lcoe_county_new['gid'].str[1:3] +  lcoe_county_new['gid'].str[4:7]

for i in lcoe_county_new['fips'].unique():
    if len(lcoe_county_new[(lcoe_county_new['fips']==i) & (lcoe_county_new['ele_tech']=='land-based-wind')] ) == 0:
        temp = lcoe_county_new[(lcoe_county_new['fips']==i) & (lcoe_county_new['ele_tech']=='pv')]
        temp['ele_tech'] = 'land-based-wind'
        temp[chosen_lcoe_input] = 51.35
        lcoe_county_new = pd.concat([lcoe_county_new,temp])
        #print(i)

#lcoe_county_new.loc[lcoe_county_new['ele_tech']=='land-based-wind',chosen_lcoe_input] = lcoe_county_new.loc[lcoe_county_new['ele_tech']=='land-based-wind',chosen_lcoe_input]  / 2.5

#inflation-adjusted adder
# RIP IRA
ptc_adder = 27.5 * 0.94
#county_wide['lcoe_wind'] = county_wide['lcoe_wind'] + ptc_adder
#county_wide['lcoe_pv'] = county_wide['lcoe_pv'] + ptc_adder
#lcoe_county_new.loc[lcoe_county_new['ele_tech']=='land-based-wind',chosen_lcoe_input] = lcoe_county_new.loc[lcoe_county_new['ele_tech']=='land-based-wind',chosen_lcoe_input] + ptc_add 2.5
lcoe_county_new.loc[lcoe_county_new['ele_tech']=='pv',chosen_lcoe_input] = lcoe_county_new.loc[lcoe_county_new['ele_tech']=='pv',chosen_lcoe_input] + ptc_adder

lcoe_county_new.to_csv(os.path.join(root_dir,"LCOH","lcoe_plot.csv"))
lcoe_county = lcoe_county_new

# filter by year
# remove battery techs
# find minimum value
# stack
lcoe_county_sub = lcoe_county[lcoe_county['year']==lcoe_year]
lcoe_county_sub = lcoe_county_sub[["fips","ele_tech",chosen_lcoe_input]]


remove_tech = ['btm','battery','coal','commercial_pv','fom','gas-cc','gas-ct','geothermal','residential_pv']
lcoe_county_nobattery = lcoe_county_sub[~lcoe_county_sub['ele_tech'].isin(remove_tech)]
lcoe_county_nobattery = lcoe_county_nobattery[lcoe_county_nobattery[chosen_lcoe_input]>0]


lcoe_county_sub = lcoe_county_sub[(lcoe_county_sub['ele_tech']=="land-based-wind") | (lcoe_county_sub['ele_tech']=='pv')]
lcoe_min = lcoe_county_nobattery.groupby('fips')[chosen_lcoe_input].min().reset_index()
lcoe_min['ele_tech'] = "min_alltechs"
lcoe_county_out = pd.concat([lcoe_min,lcoe_county_sub]).drop_duplicates().reset_index()

county_wide = lcoe_county_out.pivot(index=['fips'], columns=['ele_tech'], values=chosen_lcoe_input).reset_index()
county_wide.columns = ['fips','lcoe_wind','lcoe_min','lcoe_pv']


county_wide = pd.merge(county_wide,c2z[['fips','state_abb']],on='fips')
county_wide['state_abb'] = county_wide['state_abb'].str.lower().str.replace(' ', '')

wind_share = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","wind_share.csv"),names=['state_name','share'],header=0)
wind_share['state_name'] = wind_share['state_name'].str.lower().str.replace(' ', '')

wind_share = pd.merge(wind_share,state_name_abb,on='state_name')
county_wide = pd.merge(county_wide,wind_share[['state_abb','share']],on='state_abb',how='left')

county_wide['lcoe_blend'] = county_wide['lcoe_wind'] * county_wide['share'] + county_wide['lcoe_pv'] * (1-county_wide['share'])


#!!!! important assumption here
#!!!! can either choose the minimum (lcoe_min) or the wind/solar blend (lcoe_blend)
chosen_lcoe = "lcoe_min"


county_wide = pd.merge(county_wide,wind_share,how='left')


fuel_prices_state = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","fuel_prices_state.csv"))
fuel_prices_state['state_name'] = fuel_prices_state['State'].str.lower().str.replace(' ', '')
fuel_prices_state = pd.merge(fuel_prices_state,state_name_abb)
fuel_prices_state = fuel_prices_state[['state_abb','ELE_IND','Gas','CCS2']]
fuel_prices_state.columns = ['state_abb','grid_ele_price','gas_price','ccs_cost']

county_wide = pd.merge(county_wide,fuel_prices_state,on='state_abb')

temp_wide = county_wide[['fips','state_abb',chosen_lcoe,'grid_ele_price','gas_price','ccs_cost']]
temp_wide.columns = ['fips','state_abb','offgrid_ele_price','grid_ele_price','gas_price','ccs_cost']

h2_county = h2_char_orig.copy()
h2_county = h2_county[['pathway','cost_cap','cost_fom_per_metric_ton','ccs_cap_rate_comb','cost_vom','int_elec','int_ng']]
h2_county = h2_county.merge(county_wide, how='cross')

#compute the WACC and capital recovery factor to use in LCOF
h2_county['wacc'] = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real
#wacc_par = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real

h2_county['crf'] = (h2_county['wacc'] * (1+h2_county['wacc'])**fac_lifetime) / ( (1+h2_county['wacc'])**fac_lifetime-1 )
#crf_par = (wacc_par * (1+wacc_par)**fac_lifetime) / ( (1+wacc_par)**fac_lifetime-1 )

h2_county['cost_cap'] = h2_county['cost_cap'].astype(float)
h2_county['LCOF_cap'] = h2_county['cost_cap']/114.877/365*cdt_factor*h2_county['crf']/cap_factor
h2_county['LCOF_vom'] = h2_county['cost_vom'].astype(float)

h2_county['emit_captured'] = h2_county['ccs_cap_rate_comb'].astype(float) * 0.053 * h2_county['int_ng'].astype(float)


h2_county['LCOF_co2_tns'] = h2_county['ccs_cost'].astype(float) * h2_county['emit_captured']

#!!!! will also need expanding when looking at steel
h2_county['LCOF_energy_gas'] = h2_county['int_ng'].astype(float) * h2_county['gas_price']
# note conversion from cents per kwh to dollars per mwh via the factor of 10
h2_county['LCOF_energy_elec_ongrid'] = 10 * h2_county['int_elec'].astype(float) * h2_county['grid_ele_price'] 
h2_county['LCOF_energy_elec_wind'] = h2_county['int_elec'].astype(float) * h2_county['lcoe_wind'] 
h2_county['LCOF_energy_elec_pv'] = h2_county['int_elec'].astype(float) * h2_county['lcoe_pv'] 
h2_county['LCOF_energy_elec_min'] = h2_county['int_elec'].astype(float) * h2_county['lcoe_min'] 
h2_county['LCOF_energy_elec_blend'] = h2_county['int_elec'].astype(float) * h2_county['lcoe_blend'] 
h2_county['LCOF_fom'] = h2_county['cost_fom_per_metric_ton'].astype(float)/114.877

h2_transport_stor = pd.read_csv("/Users/max/Documents/GitHub/LCOH/raw_data/h2_transport_and_storage_costs.csv",
                                names=['type','t','parameter','value'],header=0)
h2_stor = pd.read_csv("/Users/max/Documents/GitHub/LCOH/raw_data/h2_storage_rb.csv",names=['type','ba'],header=0)

h2_stor_char = pd.merge(h2_stor,h2_transport_stor,how='left')

h2_stor_char = h2_stor_char[h2_stor_char['parameter'].isin(['cost_cap','fom'])]

h2_stor_char['LCOS'] = 0

#h2_county['LCOF_cap'] = h2_county['cost_cap']/114.877/365*cdt_factor*h2_county['crf']/cap_factor
h2_stor_char.loc[h2_stor_char['parameter']=='cost_cap','LCOS'] = (h2_stor_char['value'] / 8760 / 114.877) / 0.15

#h2_perm['LCOF_fom'] = h2_perm['cost_fom_per_metric_ton'].astype(float)/114.877
h2_stor_char.loc[h2_stor_char['parameter']=='fom','LCOS'] = h2_stor_char['value'] / 1e4


h2_stor_char = h2_stor_char[h2_stor_char['t']==lcoe_year]
h2_stor_char = h2_stor_char[['ba','parameter','LCOS']]

h2_stor_char = h2_stor_char.pivot(index='ba',columns='parameter',values='LCOS').reset_index()
h2_stor_char.columns = ['ba','LCOS_cap','LCOS_fom']

#county_wide = lcoe_county_out.pivot(index=['fips'], columns=['ele_tech'], values=chosen_lcoe).reset_index()

h2_county_withba = pd.merge(h2_county,c2z[['fips','ba']],on='fips')


h2_county = h2_county_withba.merge(h2_stor_char,on='ba',how='left')

components_county = ['LCOF_cap', 'LCOF_vom', 'LCOF_fom', 'LCOF_co2_tns','LCOF_energy_gas','LCOF_energy_elec_ongrid', 
                    'LCOF_energy_elec_wind', 'LCOF_energy_elec_pv', 'LCOF_energy_elec_min', 'LCOF_energy_elec_blend','LCOS_cap','LCOS_fom']

# find columns that aren't in components for the melt function
id_vars_county = [x for x in list(h2_county.columns) if x not in components_county]

h2_county_out = pd.melt(h2_county,value_name='LCOF_Cost',value_vars=components_county,id_vars = id_vars_county)


chosen_lcoe_offgrid = 'LCOF_energy_elec_min'

ongrid_vars = ['LCOF_cap', 'LCOF_vom', 'LCOF_fom', 'LCOF_co2_tns','LCOF_energy_gas', 'LCOF_energy_elec_ongrid','LCOS_cap','LCOS_fom']
offgrid_vars = ['LCOF_cap', 'LCOF_vom', 'LCOF_fom', 'LCOF_co2_tns','LCOF_energy_gas', 'LCOF_energy_elec_min','LCOS_cap','LCOS_fom']

h2_county_out_offgrid = h2_county_out.copy()
h2_county_out_offgrid['style'] = 'offgrid'
h2_county_out_offgrid = h2_county_out_offgrid[h2_county_out_offgrid['variable'].isin(offgrid_vars)]
h2_county_out_ongrid = h2_county_out.copy()
h2_county_out_ongrid['style'] = 'ongrid'
h2_county_out_ongrid = h2_county_out_ongrid[h2_county_out_ongrid['variable'].isin(ongrid_vars)]

h2_county_out = pd.concat([h2_county_out_ongrid,h2_county_out_offgrid])
h2_county_out.to_csv(os.path.join(root_dir,"LCOH","county_h2_out.csv"))




# --- begin LCOS by state --- #

steel_county = temp_wide.copy()
# load in ba mapping to fips and match CCS costs by column
steel_county = steel_county.merge(c2z[['fips','ba']],how='left')

# add in ore transport costs
ore_transport = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","finito_iron_ore_transport_cost.csv"),header=0)
ore_transport.columns = ore_transport.columns.str.lower()
ore_transport = ore_transport[['ba','2030']]
ore_transport.columns = ['ba','ore_transport']

steel_county = steel_county.merge(ore_transport,on='ba',how='left')

finito_prices = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","fuelprices_finito.csv"))
finito_prices['state_abb'] = finito_prices['state_abb'].str.lower().str.replace(' ','') 
finito_prices = finito_prices[finito_prices['state_abb']!='voluntary']
finito_prices = finito_prices[finito_prices['t']==lcoe_year]

finito_prices = finito_prices[['ei','state_abb','cost']]
finito_prices = finito_prices.pivot(index='state_abb',columns='ei',values='cost').reset_index()

steel_prices = steel_county.merge(finito_prices,on='state_abb',how='left')
steel_prices.columns = steel_prices.columns.str.replace("int","price")

lcoh_tech = h2_county_out.groupby(['fips','pathway','style'])['LCOF_Cost'].sum().reset_index()

#!!!! if you have LCOH by fips, tech, and on/offgrid (style).. can replace here
steel_matrix = steel_prices.merge(lcoh_tech,on='fips',how='left')

steel_char = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","char_ind.csv"))

steel_char = steel_char[steel_char['id']=='new']
steel_char = steel_char[steel_char['commodity']=='steel']

drop_steel = ["id","ba_zone","commodity","fac_id","fac_zip","lat","lon","cod","ref_cap","cap_dec","prod_2018","int_hgl","int_opet",
              "int_ng_feed","int_coal_feed","int_coke_feed","int_lighthgl_feed","int_medhgl_feed","int_heavypchem_feed",
              "int_m_limestone","int_m_cullet","int_m_silica","int_m_soda_ash"]

steel_char = steel_char.drop(drop_steel,axis=1)

wacc_par = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real
crf_par = (wacc_par * (1+wacc_par)**fac_lifetime) / ( (1+wacc_par)**fac_lifetime-1 )


steel_perm = steel_matrix.merge(steel_char,how='cross')

# -- calculate LCOE components
steel_perm['lcos_coal'] = steel_perm['int_coal'].astype(float)*steel_perm['price_coal'].astype(float)
steel_perm['lcos_met_coal'] = steel_perm['int_met_coal'].astype(float)*steel_perm['price_met_coal'].astype(float)
steel_perm['lcos_coke'] = steel_perm['int_coke'].astype(float)*steel_perm['price_coke'].astype(float)
steel_perm['lcos_ddfo'] = steel_perm['int_ddfo'].astype(float)*steel_perm['price_ddfo'].astype(float)
steel_perm['lcos_ng'] = steel_perm['int_ng'].astype(float)*steel_perm['gas_price'].astype(float)
steel_perm['lcos_elec'] = steel_perm['int_elec'].astype(float)*steel_perm['price_elec'].astype(float)
steel_perm['lcos_rfo'] = steel_perm['int_rfo'].astype(float)*steel_perm['price_rfo'].astype(float)
steel_perm['lcos_h2_feed'] = 114*steel_perm['int_h2_feed'].astype(float)*steel_perm['LCOF_Cost'].astype(float)


#assumptions from finito
steel_perm['lcos_m_scrap'] = steel_perm['int_m_scrap'].astype(float)*325
steel_perm['lcos_m_ore'] = steel_perm['int_m_ore'].astype(float)*(111.06+steel_perm['ore_transport'])

steel_perm['lcos_vom'] = steel_perm['cost_vom']

steel_perm['lcos_cap'] = steel_perm['cost_cap'].astype(float)*cdt_factor*crf_par/cap_factor
steel_perm['lcos_fom'] = steel_perm['cost_fom'].astype(float)/cap_factor


'''
*ei,value
*fuel input,combustion emissions [metric tons CO2 / MMBtu]
int_coal,0.095
int_ng,0.053
int_coke,0.113
int_hgl,0.063
int_ddfo,0.074
int_rfo,0.074
int_met_coal,0.093
'''

steel_perm['lcos_ccs'] = steel_perm['ccs_cost'].astype('float') * steel_perm['ccs_cap_rate_comb'].astype('float') * ((steel_perm['int_coal'].astype('float') * 0.095 + steel_perm['int_ng'].astype('float') * 0.053 + steel_perm['int_coke'].astype('float') * 0.113 + 
                             steel_perm['int_ddfo'].astype('float') * 0.074 + steel_perm['int_rfo'].astype('float') * 0.074 + steel_perm['int_met_coal'].astype('float') * 0.093)
                            + steel_perm['co2_rate_proc'].astype('float') )
                            
steel_char = ['lcos_coal','lcos_met_coal','lcos_coke','lcos_ddfo','lcos_ng','lcos_elec','lcos_elec','lcos_rfo','lcos_h2_feed','lcos_m_scrap','lcos_m_ore','lcos_vom','lcos_cap','lcos_fom','lcos_ccs']
steel_out = steel_perm[['fips','type','pathway','style','lcos_coal','lcos_met_coal','lcos_coke','lcos_ddfo','lcos_ng','lcos_elec','lcos_elec','lcos_rfo','lcos_h2_feed','lcos_m_scrap','lcos_m_ore','lcos_vom','lcos_cap','lcos_fom']]

steel_county = pd.melt(steel_perm,value_name='lcos',value_vars=steel_char,id_vars = ['fips','type','pathway','style'])
steel_county.to_csv(os.path.join(root_dir,'LCOH','steel_county.csv'))











#-- CAMBIUM --#
# year for cambium data
cambium_year = 2030


# here - we define a function that loads in the data for a list of balancing areas (BAs)
# that list of BAs is thread-specific and passed as an argument to the run_regions functions below
# run_regions first ranks the observations, filters up to each rank (8760 total), and takes the average LCOE across all those hours

#see: https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread
from threading import Thread

# defines number of threads to use
num_thread = 10

#create a list of all the ReEDS BAs
ba_list_full = ['p' + str(n) for n in range(1,135)]

#p119 missing, p122 actually z122
ba_list_full.remove('p119')
ba_list_full.remove('p122')
ba_list_full.append('z122')


def run_region(ba_list,results,index):
    #create an empty data frame
    cam_out = pd.DataFrame()
    #for each of the regions in ba_list    
    for r in ba_list:
        #load in the data
        cam_in = pd.read_csv(os.path.join(root_dir,'LCOH','raw_data','hourly_balancingArea','Cambium24_MidCase_hourly_'+r+'_'+str(cambium_year)+'.csv'),header=5)[['total_cost_enduse']]
        #rank each one, note 'first' implies there can be repeat values which will give us the full 8760        
        cam_in['rank'] = cam_in.rank(method='first')
        
        #for each of the uniquely-ranked items
        for i in cam_in['rank'].unique():
            # take the average over all hours up to and including that rank
            cam_temp = cam_in[cam_in['rank']<=i]['total_cost_enduse'].mean()
            #create a stackable dataframe
            cam_stack = pd.DataFrame({'avg_lcoe':[cam_temp], 'rank':[i], 'r':[r] })
            #stack the dataframe
            cam_out = pd.concat([cam_out,cam_stack])

    #add the results to the results dataframe
    results[index] = cam_out    


#divide a list up into equal lengths (except the last list)
def chunks(ba_list, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(ba_list), n):
        yield ba_list[i:i + n]

# create thread and results lists
threads = [None] * num_thread
results = [None] * num_thread


#define number of jobs per thread
num_per_thread = int(round(len(ba_list_full)/num_thread,0)+1)

#break the ba_list_full into n-sized chunks
ba_index = list(chunks(ba_list_full,num_per_thread))

# create and start threads, grabbing the appropriate list of BAs from ba_index
for i in range(len(threads)):
    threads[i] = Thread(target=run_region, args=(ba_index[i], results, i))
    threads[i].start()



# join the threads together once they're finished
for i in range(len(threads)):
    threads[i].join()

full_out = pd.DataFrame()

for i in range(len(threads)):
    full_out = pd.concat([full_out,results[i]])
    

full_out['r'] = full_out['r'].str.replace('z122', 'p122')

h2_8760 = h2_char_orig.copy()
h2_8760 = h2_8760[['pathway','cost_cap','cost_fom_per_metric_ton','ccs_cap_rate_comb','cost_vom','int_elec','int_ng']]

#h2_county = h2_county.merge(county_wide, how='cross')
ba_to_state = c2z[['ba','state_abb']].drop_duplicates()
ba_to_state.columns = ['r','state_abb']

full_out_merged = full_out.merge(ba_to_state,how='left')

full_out_merged = full_out_merged.merge(h2_8760,how='cross')

# add fuel prices, compute LCOH based on hour/capacity factor

#fuel_prices_state
full_out_merged['state_abb'] = full_out_merged['state_abb'].str.lower().str.replace(' ', '')

full_out_merged = full_out_merged.merge(fuel_prices_state,on='state_abb',how='left')

full_out_merged['cf'] = full_out_merged['rank']/8760



#h2_county['wacc'] = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real
wacc_par = (1-equity_share)*int_debt*(1-tax_rate)+equity_share*rroe_real

crf_par = (wacc_par * (1+wacc_par)**fac_lifetime) / ( (1+wacc_par)**fac_lifetime-1 )


full_out_merged['cost_cap'] = full_out_merged['cost_cap'].astype(float)
full_out_merged['LCOF_cap'] = full_out_merged['cost_cap']/114.877/365*cdt_factor * crf_par/full_out_merged['cf']
full_out_merged['LCOF_vom'] = full_out_merged['cost_vom'].astype(float)
full_out_merged['emit_captured'] = full_out_merged['ccs_cap_rate_comb'].astype(float) * 0.053 * full_out_merged['int_ng'].astype(float)
full_out_merged['LCOF_co2_tns'] = full_out_merged['ccs_cost'].astype(float) * full_out_merged['emit_captured']
full_out_merged['LCOF_energy_gas'] = full_out_merged['int_ng'].astype(float) * full_out_merged['gas_price']
# here note we're using the avg_lcoe value up to the ranked hour
full_out_merged['LCOF_energy_elec'] = full_out_merged['int_elec'].astype(float) * full_out_merged['avg_lcoe'] 
full_out_merged['LCOF_fom'] = full_out_merged['cost_fom_per_metric_ton'].astype(float)/114.877

h2_transport_stor = pd.read_csv("/Users/max/Documents/GitHub/LCOH/raw_data/h2_transport_and_storage_costs.csv",
                                names=['type','t','parameter','value'],header=0)
h2_stor = pd.read_csv("/Users/max/Documents/GitHub/LCOH/raw_data/h2_storage_rb.csv",names=['type','r'],header=0)


h2_stor_char = pd.merge(h2_stor,h2_transport_stor,how='left')

h2_stor_char = h2_stor_char[h2_stor_char['parameter'].isin(['cost_cap','fom'])]

h2_stor_char['LCOS'] = 0

#h2_county['LCOF_cap'] = h2_county['cost_cap']/114.877/365*cdt_factor*h2_county['crf']/cap_factor
h2_stor_char.loc[h2_stor_char['parameter']=='cost_cap','LCOS'] = (h2_stor_char['value'] / 8760 / 114.877) / 0.15

#h2_perm['LCOF_fom'] = h2_perm['cost_fom_per_metric_ton'].astype(float)/114.877
h2_stor_char.loc[h2_stor_char['parameter']=='fom','LCOS'] = h2_stor_char['value'] / 1e4

h2_stor_char = h2_stor_char[h2_stor_char['t']==lcoe_year]
h2_stor_char = h2_stor_char[['r','parameter','LCOS']]

h2_stor_char = h2_stor_char.pivot(index='r',columns='parameter',values='LCOS').reset_index()
h2_stor_char.columns = ['r','LCOS_cap','LCOS_fom']


full_out_merged = full_out_merged.merge(h2_stor_char,on='r',how='left')

tech_keep = ['h2_pem_electrol', 'h2_soec_electrol', 'h2_smr', 'h2_smr_ccs',
       'h2_pem_electrol_gh500', 'h2_pem_electrol_gh1000',
       'h2_pem_electrol_gh2000']

out_merged= full_out_merged[full_out_merged['pathway'].isin(tech_keep)]

col_keep = ['avg_lcoe', 'rank', 'r', 'state_abb', 'pathway', 
            'cf', 'LCOF_cap',
       'LCOF_vom', 'emit_captured', 'LCOF_co2_tns', 'LCOF_energy_gas',
       'LCOF_energy_elec_ongrid', 'LCOF_energy_elec', 'LCOF_fom', 'LCOS_cap',
       'LCOS_fom']

out_merged[col_keep].to_csv("/Users/max/Desktop/out_temp.csv",index=False)





