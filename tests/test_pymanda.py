import pytest
from pymanda import ChoiceData
import pandas
import numpy

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
    zips += [7 for x in range(10)] #in 90 psa
    zips += [8 for x in range(9)] #in 90 psa
    zips += [3 for x in range(4)] #in 75 psa
    zips += [5 for x in range(2)] #out of psa
    #corp z
    zips += [7 for x in range(10)] #in 90 psa
    zips += [10 for x in range(9)] #in 90 psa
    zips += [3 for x in range(4)] #in 75 psa
    zips += [9 for x in range(1)] #out of psa
    zips += ["" for x in range(1)] #out of psa
    
    psa_data = pd.DataFrame({'corporation': corps,
                             'choice' : choices,
                             "geography": zips})
    return psa_data

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
    with pytest.raise(ValueError):
        ChoiceData(df_empty, 'choice', corp_var='corporation', geog_var='geography')

def test_ChoiceMissing(psa_data):
    '''test for an observation missing choice'''
    df_miss = pd.DataFrame({'corporation': [""],
                             'choice' : [""],
                             "geography": [""]})
    df_miss = pd.concat([df_miss, psa_data])
    with pytest.raise(ValueError):
        ChoiceData(df_miss, 'choice', corp_var='corporation', geog_var='geography')

def test_BadCorp(psa_data):
    '''test for corporation parameter not in data'''
    with pytest.raise(ValueError):
        ChoiceData(df_miss, 'choice', corp_var='corporations', geog_var='geography')

def test_BadGeo(psa_data):
    '''test for geog_var parameter nor t in data'''
    with pytest.raise(ValueError):
        ChoiceData(df_miss, 'choice', corp_var='corporation', geog_var='zips') 
        
def test_UndefinedCorp(psa_data):
    '''test for empty corporation parameter returning as choice_var'''
    data = ChoiceData(psa_data, 'choice', geog_var='geography')
    assert ChoiceData.corp_var== "choice"
    

## Tests for estimate_psas()
@oytest.fixture
def cd_psa(psa_data):
    cd_psa = ChoiceData(psa_data, "choice", corp_var='corporation', geog_var='zips')
    return cd_psa



    