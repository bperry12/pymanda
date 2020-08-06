import pandas as pd

class ChoiceData():
    def __init__(
        self,
        data, 
        choice_var,
        corp_var= None,
        geog_var= None,
        wght_var= None):
        
        if corp_var is None:
            corp_var = choice_var
    
        self.params = {'choice_var' : choice_var,
                       'corp_var' : corp_var,
                       'geog_var' : geog_var,
                       'wght_var' : wght_var}
        
        self.data = data
        self.choice_var = choice_var
        self.corp_var = corp_var
        self.geog_var = geog_var
        self.wght_var = wght_var
        
        if type(data) !=  pd.core.frame.DataFrame:
            raise TypeError ('''Expected type pandas.core.frame.DataFrame Got {}''').format(type(data))
        
        if data.empty:
            raise ValueError ('''Dataframe is Empty''')
        
        defined_params = [x for x in [choice_var, corp_var, geog_var, wght_var] if x is not None]
        for param in defined_params:
            if param not in data.columns:
                raise KeyError ('''{} is not a column in Dataframe''').format(param)
        
        for nonull in [choice_var, corp_var]:
            if data[nonull].isnull().values.any():
                raise ValueError ('''{} has missing values''').format(nonull)
        
        
    def estimate_psa(self, centers, threshold=[.75, .9]):
        if self.geog_var is None:
            raise ValueError ("geog_var is not defined")
        
        if type(threshold) != list:
            threshold = [threshold]
        
        for alpha in threshold:
            if type(alpha) != float:
                raise TypeError ('''Expected threshold to be type float. Got {}'''.format(type(alpha)))
            if not 0 < alpha <= 1:
                raise ValueError (''''Threshold value of {} is not between 0 and 1''').format(alpha)
        
        if self.wght_var is None:
            df['count'] = 1
            self.wght_var = "count"
            
        df = self.data[self.corp_var, self.geog_var, self.wght_var]
        df = df.groupby([corp_var, geog_var]).sum().reset_index()
        df = df.sort_values([corp_var, wght_var], ascending=False)
        
        df['group_total'] = df['count'].groupby(df[corp_var]).transform('sum')
        df['share'] = df['count'] / df['group_total']
        df = df.groupby([corp_var, geog_var]).sum().groupby(level=0).cumsum().reset_index()
        
        df['keep'] = np.where(df['share'].shift().fillna(1).replace(1, 0) < .75, 1, 0)
        