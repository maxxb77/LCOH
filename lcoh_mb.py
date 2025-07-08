
import pandas as pd
import numpy as np
import os
from itertools import product

root_dir = "/Users/max/Documents/GitHub"

cf_char = pd.read_csv(os.path.join(root_dir,"FINITO","inputs","char_cf.csv"))
fuel_prices_state = pd.read_csv(os.path.join(root_dir,"LCOH","raw_data","fuel_prices_state.csv"))


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

print

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

co2_ng = [0.053, 0.064, 0.075, 0.082, 0.086, 0.111, 0.140]
#@@
#co2_ng = [0.053]

co2_tax = [0]

co2_tns = [5,15,25]
#@@
#co2_tns = [15]

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
h2_perm['LCOF_cap'] = h2_perm['cost_cap']/114.877/365*cdt_factor*h2_perm['crf']/cap_factor
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

#!!! if copying this line, need to include other components
#h2_state['emit_rate_comb'] = 0.052 * h2_state['int_ng'].astype(float)
#h2_state['emit_ele'] = 365 * h2_state['int_elec'].astype(float)
#h2_state['emit_rate_total'] = h2_state['emit_rate_comb'] + h2_state['emit_ele']
#captured emissions do not include upstream accounting
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










