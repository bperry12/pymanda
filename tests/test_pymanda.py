import pytest
from pymanda import ChoiceData
import pandas
import numpy
@pytest.fixture
def psa_data():
    '''create data for psa analysis'''
    #create corporations series
    corps = ['x' for x in range(0,50)]
    corps += ['y' for x in range(0,25)]
    corps += ['z' for x in range(0,25)]
    
    #create choice series
    #corp x
    choices = ['a' for x in range(0,30)]
    choices += ['b' for x in range(0,20)]
    #corp y
    choices += ['c' for x in range(0,20)]
    choices += ['d' for x in range(0,5)]
    #corp z
    choices += ['e' for x in range(25)]
    
    # create zips
    #corp x
    zips = [1 for x in range(0,20)] #in 75 psa
    zips += [2 for x in range(0,10)] #in 75 psa
    zips += [3 for x in range(0,8)] #in 75 psa
    zips += [4 for x in range(0,7)] #in 90 psa
    zips += [5 for x in range(0,3)] # in 90 psa
    zips += [6 for x in range(0,2)] # out of psa
    #corp y
    zips += [7 for x in range(0,10)] #in 90 psa
    zips += [8 for x in range(0,9)] #in 90 psa
    zips += [3 for x in range(0,4)] #in 75 psa
    zips += [5 for x in range(0,2)] #out of psa

    #corp z
    zips += [7 for x in range(0,10)] #in 90 psa
    zips += [10 for x in range(0,9)] #in 90 psa
    zips += [3 for x in range(0,4)] #in 75 psa
    zips += [9 for x in range(0,1)] #out of psa
    zips += ["" for x in range(0,1)] #out of psa
    
    
    psa_data = pd.DataFrame({'corporation': })


def test_ChoiceData_BadInput():
    '''Test for error catching bad input'''
    with pytest.raises(TypeError):
        ChoiceData(["bad", "input"]) 

def test_ChoiceData_GoodInput():
    '''test for accepting pandas dataframe'''
    