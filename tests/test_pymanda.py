import pytest
from pymanda import ChoiceData
import pandas as pd
import numpy as np

@pytest.fixture
def psa_data():
    '''create data for psa analysis'''
    #create corporations series
    corps = ['x' for x in range(50)]
    corps += ['y' for x in range(25)]
    corps += ['z' for x in range(25)]
    
    #create choice series
    #corp x
    choices = ['a' for x in range(30)]
    choices += ['b' for x in range(20)]
    #corp y
    choices += ['c' for x in range(20)]
    choices += ['d' for x in range(5)]
    #corp z
    choices += ['e' for x in range(25)]
    
    # create zips
    #corp x
    zips = [1 for x in range(20)] #in 75 psa
    zips += [2 for x in range(10)] #in 75 psa
    zips += [3 for x in range(8)] #in 75 psa
    zips += [4 for x in range(7)] #in 90 psa
    zips += [5 for x in range(3)] # in 90 psa
    zips += [6 for x in range(2)] # out of psa
    #corp y
    zips += [7 for x in range(10)] #in 75 psa
    zips += [8 for x in range(9)] #in 75 psa
    zips += [3 for x in range(4)] #in 90 psa
    zips += [5 for x in range(2)] #out of psa
    #corp z
    zips += [7 for x in range(10)] #in 75 psa
    zips += [10 for x in range(9)] #in 75 psa
    zips += [3 for x in range(4)] #in 90 psa
    zips += [9 for x in range(1)] #out of psa
    zips += ["" for x in range(1)] #out of psa
    
    psa_data = pd.DataFrame({'corporation': corps,
                             'choice' : choices,
                             "geography": zips})
    
    return psa_data

@pytest.fixture()
def onechoice_data():
    choices = ['a' for x in range(100)]
    
    zips = [1 for x in range(20)]
    zips += [2 for x in range(20)]
    zips += [3 for x in range(20)]
    zips += [4 for x in range(20)]
    zips += [5 for x in range(20)]
    
    wght = [1.5 for x in range(20)]
    wght += [1 for x in range(20)]
    wght += [.75 for x in range(20)]
    wght += [.5 for x in range(20)]
    wght += [.25 for x in range(20)]
    
    onechoice_data = pd.DataFrame({'choice': choices,
                                   'geography': zips,
                                   'weight' : wght})
    return onechoice_data
    
## Tests for ChoiceData Initialization
def test_BadInput():
    '''Test for error catching bad input'''
    with pytest.raises(TypeError):
        ChoiceData(["bad", "input"]) 

def test_AllMissing():
    '''test for empty dataframe'''
    df_empty = pd.DataFrame({'corporation': [],
                             'choice' : [],
                             "geography": []})
    with pytest.raises(ValueError):
        ChoiceData(df_empty, 'choice', corp_var='corporation', geog_var='geography')

def test_ChoiceMissing(psa_data):
    '''test for an observation missing choice'''
    df_miss = pd.DataFrame({'corporation': [""],
                             'choice' : [""],
                             "geography": [""]})
    df_miss = pd.concat([df_miss, psa_data])
    with pytest.raises(ValueError):
        ChoiceData(df_miss, 'choice', corp_var='corporation', geog_var='geography')

def test_BadCorp(psa_data):
    '''test for corporation parameter not in data'''
    with pytest.raises(KeyError):
        ChoiceData(psa_data, 'choice', corp_var='corporations', geog_var='geography')

def test_BadGeo(psa_data):
    '''test for geog_var parameter not in data'''
    with pytest.raises(KeyError):
        ChoiceData(psa_data, 'choice', corp_var='corporation', geog_var='zips') 
        
def test_UndefinedCorp(psa_data):
    '''test for empty corporation parameter returning as choice_var'''
    data = ChoiceData(psa_data, 'choice', geog_var='geography')
    assert data.corp_var== "choice"
    

## Tests for estimate_psas()
@pytest.fixture
def cd_psa(psa_data):
    cd_psa = ChoiceData(psa_data, "choice", corp_var='corporation', geog_var='geography')
    return cd_psa

def test_define_geogvar(psa_data):
    '''Test for error raising if geography variable is not defined'''
    bad_cd = ChoiceData(psa_data, "choice", corp_var='corporation')
    with pytest.raises(KeyError):
        bad_cd.estimate_psa(["x"])

def test_BadThreshold(cd_psa):
    '''Test for error raising if thresholds are not between 0 and 1'''
    with pytest.raises(TypeError):
        cd_psa.estimate_psa(['x'], threshold=[.75, .9, 75])

def test_BadCenters(cd_psa):
    '''Test for if psa centers are not in corp_var'''
    with pytest.raises(ValueError):
        cd_psa.estimate_psa(['a'])

def test_3Corp(cd_psa):
    '''Estimate the 3 Corporations in the psa data with default parameters'''
    psa_dict = cd_psa.estimate_psa(['x', 'y', 'z'])
    
    answer_dict = {'x_0.75': [1,2,3],
                   'x_0.9': [1,2,3,4],
                   'y_0.75': [7,8],
                   'y_0.9': [3,7,8],
                   'z_0.75': [7,10],
                   'z_0.9' : [3,7,10]}
    
    assert answer_dict==psa_dict

def test_1corp(cd_psa):
    '''Estimate the 1 Corporation in the psa data with default parameters'''
    psa_dict = cd_psa.estimate_psa(['x'])
    
    answer_dict = {'x_0.75': [1,2,3],
                   'x_0.9': [1,2,3,4]}
    
    assert answer_dict==psa_dict
    
def test_1corp_weight(onechoice_data):
    ''' Estimate PSAs for 1 corporation with weight var and custom threshold'''
    cd_onechoice = ChoiceData(onechoice_data, 'choice', geog_var='geography', wght_var='weight')
    
    psa_dict = cd_onechoice.estimate_psa(['a'], threshold=.6)
    
    answer_dict = {'a_0.6': [1,2]}
    
    assert psa_dict==answer_dict
    
def test_MultipleThresholds(onechoice_data):
    ''' Estimate PSAs for multiple custom thresholds'''
    cd_onechoice = ChoiceData(onechoice_data, 'choice', geog_var='geography', wght_var='weight')
    
    psa_dict = cd_onechoice.estimate_psa(['a'], threshold=[.6, .7])
    
    answer_dict = {'a_0.6': [1,2],
                   'a_0.7': [1,2,3]}
    
    assert psa_dict == answer_dict

##Tests for restrict_data
def test_RestrictData(psa_data, cd_psa):
    '''Check if restrict data restricts data properly'''
    cd_psa.restrict_data(psa_data['corporation']=='x')
    
    restricted_data = psa_data[psa_data['corporation']=='x']
    cd_restricted = ChoiceData(restricted_data, "choice", corp_var='corporation', geog_var='geography')
    assert cd_restricted.data.equals(restricted_data)
    
def test_BadSeries(cd_psa, psa_data):
    '''Restrict_data should only accept boolean series'''
    flag_series = np.where(psa_data['corporation']=='x', 1, 0)
    with pytest.raises(TypeError):
        cd_psa.restrict_data(flag_series)

# Tests for calculate shares
def dictionary_comparison(dict1, dict2):
    if len(dict1.keys()) == 0 or len(dict2.keys()) == 0:
        raise ValueError("Comparisons have 0 Keys")
    
    matches = []
    if dict1.keys == dict2.keys:
        for key in dict1.keys:
            matches.append(dict1[key].equals(dict2[key])) 
    
    return all(matches)

def test_BaseShares(cd_psa):
    test_shares = cd_psa.calculate_shares()
    actual_shares = {'Base Shares': pd.DataFrame({'corporation':['x', 'x', 'y', 'y', 'z'],
                                                   'choice': ['a', 'b', 'c', 'd', 'e'],
                                                   'share': [.3, .2, .2, .05, .25]})}
    
    assert dictionary_comparison(test_shares, actual_shares)
    
def test_PsaShares(cd_psa):
    psa_test = {'x_0.75': [1,2,3]}
    test_shares = cd_psa.calculate_shares(psa_test)
    
    actual_shares = {'x_0.75': pd.DataFrame({'corporation': ['x', 'x', 'y', 'y', 'z'],
                                            'choice': ['a', 'b', 'c', 'd', 'e'],
                                            'share': [x / 46 for x in [30, 8, 1,3, 4]]})}
    
    assert dictionary_comparison(test_shares, actual_shares)

#test for calculating HHI shares
@pytest.fixture
def base_shares():
    base_shares = pd.DataFrame({'corporation':['x', 'x', 'y', 'y', 'z'],
                                'choice': ['a', 'b', 'c', 'd', 'e'],
                                'share': [.3, .2, .2, .05, .25]})
    return base_shares

@pytest.fixture
def psa_shares():
    psa_shares = pd.DataFrame({'corporation': ['x', 'x', 'y', 'y', 'z'],
                                'choice': ['a', 'b', 'c', 'd', 'e'],
                                'share': [x / 46 for x in [30, 8, 1,3, 4]]})
    return psa_shares

def test_HHIs(cd_psa, base_shares, psa_shares):
    share_tables = {'Base Shares': base_shares,
                    'x_0.75': psa_shares}
    
    test_hhis = cd_psa.calculate_hhi(share_tables)
    
    actual_hhis = {'Base Shares': 3750.0,
                  'x_0.75': 7669561259911983 / 1099511627776} # approximately 6975.43
    
    assert test_hhis == actual_hhis
    
# test for calculating changes in HHI
def test_HHIChange(cd_psa, base_shares, psa_shares):
    share_dict = {'Base Shares': base_shares,
                  'x_0.75': psa_shares}
    test_change = cd_psa.hhi_change(['y', 'z'], share_dict)
    
    actual_change = {'Base Shares': 1250,
                     'x_0.75' : 166277750892401 / 1099511627776} # approximately 151.23
    
    assert test_change == actual_change
    