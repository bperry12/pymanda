# import pymanda
import pandas as pd
import numpy as np
import warnings


"""
ChoiceData
---------
A container for a DataFrame that maintains relevant columns for mergers and
acquisitions analyses

"""
class ChoiceData():
    
    """
     Two-dimensional, size-mutable, potentially heterogeneous tabular data.
    
     Data structure also contains labeled axes (rows and columns).
     Arithmetic operations align on both row and column labels. Can be
     thought of as a dict-like container for Series objects. The primary
     pandas data structure.
     
     Additionally, has parameters to identify variables of interest for 
     calculating competition metrics using customer level data
    
     Parameters
     ----------
     data : Non-Empty pandas.core.frame.DataFrame object
     choice_var : String of Column Name
         Column name that identifies the "choice" of each customer  
     corp_var : String of Column Name, default None
         Column Name that identifies a higher level classification of Choice    
     geog_var : String of Column Name, default None
         Column name that identifies a geography for Customer
     wght_var : String of Column Name, default None
         Column name that identifies weight for customer level
    
     Examples
     --------
     Constructing ChoiceData from a DataFrame.
     
     >>> choices = ['a' for x in range(100)]
     
     >>> data = pandas.DataFrame({'choice': choices})
     >>> cd = pymanda.ChoiceData(data, 'choice')
     """
    
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
            raise TypeError ('''Expected type pandas.core.frame.DataFrame Got {}'''.format(type(data)))
        
        if data.empty:
            raise ValueError ('''Dataframe is Empty''')
        
        defined_params = [x for x in [choice_var, corp_var, geog_var, wght_var] if x is not None]
        for param in defined_params:
            if param not in data.columns:
                raise KeyError ('''{} is not a column in Dataframe'''.format(param))
        
        for nonull in [choice_var, corp_var]:
            if len(data[data[self.choice_var] == ''].index) != 0:
                raise ValueError ('''{} has missing values'''.format(nonull))
     
    def corp_map(self):
        """
        Utility fuction to map corporation and choices in self.data

        Returns
        -------
        corp_map : pandas.core.frame.DataFrame
            2 column data frame with corporation name and choice names.

        """
        if self.corp_var == self.choice_var:
            raise RuntimeError('''corp_map should only be called when self.corp_var is defined and different than self.choice_var''')
        corp_map = self.data.groupby([self.corp_var, self.choice_var]).count()
        corp_map = corp_map.reset_index()
        corp_map = corp_map[[self.corp_var, self.choice_var]]
        
        return corp_map
    
    def estimate_psa(self, centers, threshold=[.75, .9]):
        """
        Return a dictionary idenftifying geographies in a choice's Primary 
        Service Area (PSA) at a given threshold.

        Dictionary keys are labeled as "{center}_{threshold}" and values are 
        a list of geographies falling within the threshold
        
        Default will use self.corp_var as choice and self.wght_var for count
        
        Parameters
        ----------
        centers: List of choices to find 
            
        threshold : float or list of floats, 
            Threshold or levels of thresholds to find the PSA for each choice 
            in centers. Default calculates 75% and 90% PSAs.

        Returns
        -------
        Dictionary
            Dictionary keys are labeled as "{center}_{threshold}" and 
            values are a list of geographies falling within the threshold
        
        Examples
        --------
        >>> choices = ['a' for x in range(100)]
        
        >>> zips = [1 for x in range(20)]
        >>> zips += [2 for x in range(20)]
        >>> zips += [3 for x in range(20)]
        >>> zips += [4 for x in range(20)]
        >>> zips += [5 for x in range(20)]
        
        >>> data = pd.DataFrame({'choice': choices, 'geography': zips})
        >>> cd = ChoiceData(data, 'choice', geog_var = 'geography')
        >>> cd.estimate_psa(['a'])
        {'a_0.75': [1, 2, 3, 4], 'a_0.9': [1, 2, 3, 4, 5]}
        
        """
        if self.geog_var is None:
            raise KeyError ("geog_var is not defined")
        
        if type(threshold) != list:
            threshold = [threshold]
        
        if type(centers) != list:
            centers = [centers]
        
        for center in centers:
            if not self.data[self.corp_var].isin([center]).any():
                raise ValueError ("{cen} is not in {corp}".format(cen=center, corp=self.corp_var))
        
        for alpha in threshold:
            if type(alpha) != float:
                raise TypeError ('''Expected threshold to be type float. Got {}'''.format(type(alpha)))
            if not 0 < alpha <= 1:
                raise ValueError ('''Threshold value of {} is not between 0 and 1''').format(alpha)
        
        df = self.data.copy(deep=True)
        if self.wght_var is None:
            df['count'] = 1
            weight = 'count'
        else:
            weight = self.wght_var
            
        df = df[[self.corp_var, self.geog_var, weight]]
     
        df = df.groupby([self.corp_var, self.geog_var]).sum().reset_index() #calculate counts by geography
        
        df['group_total'] = df[weight].groupby(df[self.corp_var]).transform('sum')  #get group totals
        df['share'] = df[weight] / df['group_total'] # calculate share
        df = df.groupby([self.corp_var, self.geog_var]).sum()
        df = df.sort_values([self.corp_var, weight], ascending=False)
        df_start = df.groupby(level=0).cumsum().reset_index() 
        
        output_dict = {}
        for alpha in threshold:
            df = df_start
            df['keep'] = np.where(df['share'].shift().fillna(1).replace(1, 0) < alpha, 1, 0)
            
            df = df[(df[self.corp_var].isin(centers)) & (df['keep']==1)]
            
            for center in centers:
                in_psa = list(df[self.geog_var][df[self.corp_var]==center])
                in_psa.sort()
                output_dict.update({"{cen}_{a}".format(cen=center, a=alpha) : in_psa})
                
        return output_dict
    
    def _export(self, file_path, output_type, output, sheet_name=None):
        """
        Utility function for exporting data.
        """
        accepted_types  = ["csv", "excel"]
        if output_type not in accepted_types:
            raise KeyError("{input} is not a supported format. Valid export options are {list}".format(input=output_type, list=accepted_types))
           
        if output_type == "csv":
            output.to_csv(file_path)
        
        elif output_type == "excel":
            try:
                with pd.ExcelWriter(file_path, mode="a", engine="openpyxl") as writer:
                    try:
                        workbook = writer.book
                        workbook.remove(workbook[sheet_name])
                    except KeyError:
                        pass
                    finally:    
                        output.to_excel(writer, sheet_name=sheet_name, index=False)
            except FileNotFoundError:
                with pd.ExcelWriter(file_path, mode="w", engine="openpyxl") as writer:
                        output.to_excel(writer, sheet_name=sheet_name, index=False)
                 
    def export_psas(self, output_dict, export=True, output_type=None, file_path=None, sheet_name="psas"):
        """
        Format PSA dictionaries from ChoiceData.estimate_psa() to be in 1 
        dataframe for export

        Parameters
        ----------
        output_dict : dict
            Output from ChoiceData.estimate_psa().
        export : Boolean, optional
            Boolean to export the data. The default is True. 
        output_type : str, optional
            File format to export data in. The default is None.
        file_path : str, optional
            Destination to save output if export=True. The default is None.    
        sheet_name : TYPE, optional
            Optional naming parameter. Only supported for output_type="excel".
            The default is "psas".

        Returns
        -------
        output : pandas.core.frame.DataFrame
            Pandas dataframe of output. Only returned when export=False.

        """        
        
        if type(export) != bool:
            raise ValueError("Export parameter must be type bool")
        
        output = pd.DataFrame()
        for key in output_dict.keys():
            psa = pd.DataFrame(index=output_dict[key])
            psa[key] = 1
            output = output.merge(psa, how='outer', left_index=True, right_index=True)
        
        output = output.fillna(0)
        output.index.name = self.geog_var
        
        output = output[output.columns.sort_values()]
        output = output.reset_index()
        if export:
            self._export(file_path, output_type, output, sheet_name)

        else:
            return output
        
        
    def restriction_checks(self, restriction):
        """
        Checks for custom restrictions
        """
        
        if type(restriction) != pd.core.series.Series:
            raise TypeError ("Expected type pandas.core.series.Series. Got {}".format(type(restriction)))
        
        if restriction.dtype != np.dtype('bool'):
            raise TypeError ("Expected dtype('bool'). Got {}".format(restriction.dtype))
            
    def restrict_data(self, restriction):
        """
        Restrict the data is self.data using an inline series
        
        Parameters
        ----------
        restriction: pandas.core.series.Series with dtyoe=Boolean
            Boolean series identifying which rows to keep given a restriction
        
        Examples
        --------
        >>> choices = ['a' for x in range(10)]
        
        >>> zips = [1 for x in range(2)]
        >>> zips += [2 for x in range(2)]
        >>> zips += [3 for x in range(2)]
        >>> zips += [4 for x in range(2)]
        >>> zips += [5 for x in range(2)]
        
        >>> data = pd.DataFrame({'choice': choices, 'geography': zips})
        >>> cd = ChoiceData(data, 'choice')
        >>> cd.data
          choice  geography
        0      a          1
        1      a          1
        2      a          2
        3      a          2
        4      a          3
        5      a          3
        6      a          4
        7      a          4
        8      a          5
        9      a          5
        >>> cd.restrict_data(data['geography'] != 5)
        >>> cd.data
          choice  geography
        0      a          1
        1      a          1
        2      a          2
        3      a          2
        4      a          3
        5      a          3
        6      a          4
        7      a          4
        
        """

        self.restriction_checks(restriction)
        
        self.data = self.data[restriction]
        
    def calculate_shares(self, psa_dict=None, weight_var=None, restriction=None):
        """
        Create Share Table of values in self.wght_var by self.choice_var
        
        Parameters
        ----------
        psa_dict: dictionary
            dictionary of lists that contain values to be kept in self.geog_var
            If None, calculates shares for full data.
            
        weight_var : str, Optional
            Column Name in self.data to use as weight. Default is None, 
            weighting every observation equally
        
        restriction: pandas.core.series.Series with dtyoe=Boolean
            Optional restriction to be applied to data before calculating 
            shares

        Returns
        -------
        Dictionary
            keys are the same as psa_dict if given or "Base Shares"
            values are corresponding pandas dataframes of the shares
        
        Examples
        --------
    
        >>> choices = ['a' for x in range(30)]
        >>> choices += ['b' for x in range(20)]
        >>> choices += ['c' for x in range(20)]
        >>> choices += ['d' for x in range(5)]
        >>> choices += ['e' for x in range(25)]
        >>> df = pd.DataFrame({choice" : choices})
        >>> cd = ChoiceData(df, "choice")
        
        >>> cd.calculate_shares()
        {'Base Shares':   choice  share
         0      a   0.30
         1      b   0.20
         2      c   0.20
         3      d   0.05
         4      e   0.25}

        """

        if type(psa_dict) != dict and psa_dict is not None:
            raise TypeError ("Expected type dict. Got {}".format(type(psa_dict)))
            
        if restriction is not None:
            self.restriction_checks(restriction)
        
        if weight_var is None:
            weight_var= self.wght_var
        if weight_var not in self.data.columns and weight_var is not None:
            raise KeyError("{} is not a Column in ChoiceData".format(weight_var))
        
        if psa_dict is None:
            psa_dict= {'Base Shares': []}
            base_shares = True
        else:
            if self.geog_var is None:
                raise ValueError ("geog_var is not defined in ChoiceData")
            elif self.geog_var not in self.data.columns:
                raise KeyError("geog_var is not in ChoiceData")
            base_shares = False
            
        if self.corp_var == self.choice_var:
            group = [self.choice_var]
        else:
            group = [self.corp_var, self.choice_var]
        
        output_dict = {}
        for key in psa_dict.keys():
            df = self.data.copy(deep=True)
            
            redefine_weight=False
            if weight_var is None:
                df['count'] = 1
                weight_var = 'count'
                redefine_weight=True
                
            if restriction is not None:
                df = df[restriction]
                
            if not base_shares:
                for geo in psa_dict[key]:
                     if not df[self.geog_var].isin([geo]).any():
                         raise ValueError ("{g} is not in {col}".format(g=geo, col=self.geog_var)) 
                df = df[df[self.geog_var].isin(psa_dict[key])]

            df = df[group + [weight_var]]
            df_shares = df.groupby(group).sum().reset_index()
            df_shares[weight_var +  "_share"] = df_shares[weight_var] / df_shares[weight_var].sum()
            output_dict.update({key: df_shares})
            
            if redefine_weight:
                weight_var = None

        return output_dict
        
    def shares_checks(self, df, share_col, data="Data"):
        """
        Checks for columns that are supposed to contain shares

        Parameters
        ----------
        df : pandas.core.frame.DataFrame()
            Dataframe containing share_col
        share_col : str
            Name of column in data frame to chekc.
        data : str, optional
            Name of parameter being checked for Error Message.
            The default is "Data".

        """
        
        if share_col not in df.columns:
            raise KeyError("Column '{}' not in ChoiceData".format(share_col))
        if (df[share_col] < 0).any():
            raise ValueError ("Values of '{col}' in {d} contain negative values".format(col=share_col, d=data))
        if df[share_col].sum() != 1:
            raise ValueError ("Values of '{col}' in {d} do not sum to 1".format(col=share_col, d=data))
    
    def export_shares(self, output_dict, export=True, output_type="excel", file_path=None):
        """
        Formatting options for calculate_shares() output

        Parameters
        ----------
        output_dict : dictionary
            Output from ChoiceData.calculate_shares().
        export : Bool, optional
            Boolean to export data. The default is True.
        output_type : string, optional
            Export file format. The default is "excel".
        file_path : string, optional
            Destination to export files. The default is None.

        """
        if type(export) != bool:
            raise ValueError("Export parameter must be type bool")
            
        if output_type =="csv" and len(output_dict.keys())>1:
            raise KeyError("Output type 'csv' is not supported for multiple share tables. Use output_type='excel'.")

        df_keys = pd.DataFrame({'keys': list(output_dict.keys())})
        split_keys = df_keys['keys'].str.rsplit("_", n=1, expand=True)
        df_keys = pd.concat([df_keys, split_keys], axis=1)
        choices = list(split_keys.groupby(0).min().index)
        
        final_out = {}
        for choice in choices:
            keep_keys = list(df_keys[df_keys[0].isin([choice])]['keys'])
            
            if self.corp_var != self.choice_var:
                base_df = self.corp_map()
                merge_vars = [self.corp_var, self.choice_var]
            else:
                base_df = pd.DataFrame({self.choice_var: self.data[self.choice_var].unique()})
                merge_vars = [self.choice_var]
            
            #combine dictionary outputs with the same choice as center
            keep_keys.sort() # places lower thresholds first
            for key in keep_keys:
                thres = key.rsplit("_")[-1]
                merge_df = output_dict[key].copy()
                cols = merge_df.columns[-2:]
                cols = [x + "_{}".format(thres) for x in cols]
                
                merge_df.columns = merge_vars + cols
                base_df = base_df.merge(merge_df, how='left', on=merge_vars)
            
            # add totals and sort by highest threshold 
            if self.corp_var != self.choice_var:
                corp_shares = base_df.groupby(self.corp_var).sum().reset_index()
                corp_shares[self.choice_var] = "AAAAA"
                base_df = base_df.append(corp_shares)
                
                sort_col = corp_shares.columns[-2]
                corp_sort = corp_shares[[self.corp_var, sort_col]] # sort on highest threshold
                corp_sort = corp_sort.rename(columns={sort_col: "subtotal sorter"})
                base_df = base_df.merge(corp_sort, how='left', on=self.corp_var)
                
                base_df = base_df.fillna(0)
                
                base_df.sort_values(['subtotal sorter',  self.corp_var, sort_col, self.choice_var], ascending=[False, True, False, True], inplace= True)
                base_df = base_df.drop(columns="subtotal sorter")
                base_df[self.choice_var] = base_df[self.choice_var].str.replace("AAAAA", "Total")
                
            else:
                sort_col = base_df.columns[-1]
                base_df = base_df.sort_values(sort_col, ascending=False)
                
            base_df = base_df.reset_index(drop=True)
            
            # add a total row
            sums = pd.DataFrame({"totals": base_df.sum()})
            sums = sums.T
            sums = sums.drop(columns=merge_vars)
            if self.corp_var != self.choice_var:
                sums = sums / 2
            num_cols = list(sums.columns)
            for col in merge_vars:
                sums[col]= "Total"
            sums = sums[merge_vars + num_cols]
            
            base_df = sums.append(base_df)
            
            rowcheck = base_df[base_df.columns[list(~base_df.columns.isin(merge_vars))]]
            
            base_df = base_df[rowcheck.sum(axis=1) != 0]
            final_out.update({choice: base_df})
                 
        if export:
            for key in final_out.keys():
                output = final_out[key]
                self._export(file_path, output_type, output, sheet_name=key)
        else:
            return final_out

     
    def calculate_hhi(self, shares_dict, share_col="count_share", group_col=None):
        """
        Calculates HHIs from precalculated shares at the corporation level
        
        Parameters
        ----------
        shares_dict: dictionary of share tables
            
        share_col : Column name in dataframe, Optional
            column that holds float of shares. Default is 'share'
        
        group_col: Column name in dataframe, Optional
            column of names to calculate HHI on. Default is self.corp_var

        Returns
        -------
        Dictionary
            keys are the same as shares_dict
            values are hhis
        
        Examples
        --------
        >>> corps = ['x' for x in range(50)]
        >>> corps += ['y' for x in range(25)]
        >>> corps += ['z' for x in range(25)]
        
        >>> choices = ['a' for x in range(30)]
        >>> choices += ['b' for x in range(20)]
        >>> choices += ['c' for x in range(20)]
        >>> choices += ['d' for x in range(5)]
        >>> choices += ['e' for x in range(25)]
        >>> df = pd.DataFrame({"corporation": corps,
                          "choice" : choices})
        >>> cd = ChoiceData(df, "choice", corp_var="corporation")
        
        >>> shares = cd.calculate_shares()
        >>> cd.calculate_hhi(shares)
        {'Base Shares': 3750.0}

        """
        if type(shares_dict) != dict:
            raise TypeError ("Expected type dict. Got {}".format(type(shares_dict)))
        
        if group_col is None:
            group_col = self.corp_var
        elif group_col not in self.data.columns:
            raise KeyError ('''"{}" is not a column in ChoiceData'''.format(group_col))
        output_dict = {}
        for key in shares_dict.keys():
            df = shares_dict[key]
            
            if type(df) != pd.core.frame.DataFrame:
                raise TypeError ('''Expected type pandas.core.frame.DataFrame Got {}'''.format(type(df)))
            
            self.shares_checks(df, share_col, data=key)
            
            df = df.groupby(group_col).sum()
            hhi = (df[share_col] * df[share_col]).sum()*10000
            
            output_dict.update({key: hhi})
            
        return output_dict
    
    def hhi_change(self, trans_dict, shares, trans_var=None, share_col="count_share"):
        """
        Calculates change in Herfindahl-Hirschman Index (HHI) from combining 
        a set of choices. Will always calculate HHI based on corp_var

        Parameters
        ----------
        trans_list : dict
            dict of lists with combinations of choices that will be combined 
            for calculating combined hhi. Elements of combinations are expected
            be in the trans_var column. 
        shares : dict
            dictoinary of dataframes of shares to calculate HHIs on.
        trans_var : str, optional
            Column name containging objects in trans_list. The default (None) 
            uses self.corp_var.
        share_col : str, optional
            Column name containing values of share. The default is "share".

        Returns
        -------
        dictionary
            key(s) will match shares parameter
            values will be a list of [pre-merge HHI, post-merge HHI, HHI change].
        """
        if trans_var is None:
            trans_var = self.corp_var
        if type(trans_dict) != dict:
            raise TypeError ('''trans_dict is expected to be dict. Got {}'''.format(type(trans_dict)))
            
        for key in trans_dict.keys():
            trans_list = trans_dict[key]

            if type(trans_list) != list:
                raise TypeError ('''Elements of trans_dict are expected to be list. Got {}'''.format(type(trans_list)))

            if len(trans_list) < 2:
                raise ValueError ('''Elements of trans_dict need atleast 2 elements to compare HHI change''')
            
            for elm in trans_list:
                if not self.data[trans_var].isin([elm]).any():
                    raise ValueError ('''{element} is not an element in column {col}'''.format(element=elm, col=trans_var))
            
        output_dict = {}
        hhi_index = ['Pre-Merger HHI', 'Post-Merger HHI', 'HHI Change']
        for trans_key in trans_dict.keys():
            trans_list = trans_dict[trans_key]
            output = pd.DataFrame(index=hhi_index)
            
            
            for key in shares.keys():
                df = shares[key].copy()
                self.shares_checks(df, share_col, data=key)
                
                if trans_var not in df.columns:
                    raise KeyError ('''{var} is not column name in {data}'''.format(var=trans_var, data=key))    
                
                pre_hhi = self.calculate_hhi({"x" : df}, share_col, group_col=self.corp_var)['x']
                
                post_df = df
                post_df[self.corp_var] = post_df[self.corp_var].where(~post_df[trans_var].isin(trans_list), 'combined')
                post_hhi = self.calculate_hhi({"x": post_df}, share_col, group_col=self.corp_var)['x']
                
                hhi_change = post_hhi - pre_hhi
                
                out_df = pd.DataFrame({key : [pre_hhi, post_hhi, hhi_change]}, index=hhi_index)
                output = output.merge(out_df, how="inner", left_index=True, right_index=True)
            
            output = output[output.columns.sort_values()]
                
            output_dict.update({trans_key: output})
            
        return output_dict
      
    def export_hhi_change(self, output_dict, export=True, output_type="excel", file_path=None, sheet_name="HHI Change"):
        """
        Formatting options for calculate_shares() output

        Parameters
        ----------
        output_dict : dictionary
            Output from ChoiceData.calculate_shares().
        export : Bool, optional
            Boolean to export data. The default is True.
        output_type : string, optional
            Export file format. The default is "excel".
        file_path : string, optional
            Destination to export files. The default is None.

        """
        if type(export) != bool:
            raise ValueError("Export parameter must be type bool")
                   
        if export:
            for key in output_dict.keys():
                out = output_dict[key]
                out = out.reset_index()
                self._export(file_path, output_type, out, sheet_name=key)
        else:
            return output_dict
        
class DiscreteChoice():
    """
    
    DiscreteChoice
    ---------
    A solver for estimating discrete choice models and post-estimation 
    analysis.     

    Parameters
    ----------
    solver: str of solver to use
    copy_x: Bool, Optional
        whether to create copies of data in calculations. Default is True.
    coef_order: list, Optional
        coefficient order used for solver 'semiparametric'
    verbose: Boolean, Optional
        Verbosity in solvers. Default is False
    min_bin: int or float, Optional
        Minimum bin size used for solver 'semiparametric'
    
    Examples
    --------
    
    DiscreteChoice(solver='semiparametric', coef_order = ['x1', 'x2', 'x3'])

    """
    def __init__(
        self,
        solver='semiperametric', 
        copy_x=True,
        coef_order= None,
        verbose= False,
        min_bin= 25):
        
        self.params = {'solver' : solver,
                       'copy_x' : True,
                       'coef_order' : coef_order,
                       'verbose': verbose,
                       'min_bin': min_bin}
        
        self.solver = solver
        self.copy_x = copy_x
        self.coef_order = coef_order
        self.verbose = verbose
        self.min_bin = min_bin
        
        current_solvers = ['semiparametric']
        if solver not in current_solvers:
            raise ValueError ('''{a} is not supported solver. Solvers currently supported are {b}'''.format(a=solver, b=current_solvers))
        
        if type(copy_x) is not bool:
            raise ValueError ('''{} is not bool type.'''.format(copy_x))
        
        if type(coef_order) != list:
            raise ValueError ('''coef_order expected to be list. got {}'''.format(type(coef_order)))
        if len(coef_order) ==0:
            raise ValueError ('''coef_order must be a non-empty list''')
        
        if type(verbose) is not bool:
            raise ValueError ('''{} is not bool type.'''.format(verbose))
        
        if type(min_bin) != float and type(min_bin) != int:
            raise ValueError('''min_bin must be a numeric value greater than 0''')
        if min_bin <= 0:
            raise ValueError('''min_bin must be greater than 0''') 
    
    def check_is_fitted(self):
        """
        Check that an Instance has been fitted

        """
        
        try:
            self.coef_
        except AttributeError:
            raise RuntimeError('''Instance of DiscreteChoice is not fitted''')
    
    def fit(self, cd, use_corp=False):
        """
        Fit Estimator using ChoiceData and specified solver

        Parameters
        ----------
        cd : pymanda.ChoiceData
            Contains data to be fitted using DiscreteChoice
        use_corp: Boolean
            Whether to fit using corp_var as choice. Default is False.

        """
        
        # if type(cd) !=  pymanda.ChoiceData:
        #     raise TypeError ('''Expected type pymanda.choices.ChoiceData Got {}'''.format(type(cd)))
            
        for coef in self.coef_order:
            if coef not in cd.data.columns:
                raise KeyError ('''{} is not a column in ChoiceData'''.format(coef))
                
        if use_corp:
            choice= cd.corp_var
            self._used_corp = True
        else:
            choice= cd.choice_var
            self._used_corp = False

        # currently only supports 'semiparametric' solver. Added solvers should use elif statement
        if self.solver=='semiparametric':
            
            X = cd.data[self.coef_order + [choice]].copy()
            
            if cd.wght_var is not None:
                X['wght'] = cd.data[cd.wght_var]
            else:
                X['wght'] = 1
                
            ## group observations
            X['grouped'] = False
            X['group'] = ""
            for i in range(4, len(self.coef_order)+4):
                bin_by_cols = X.columns[0:-i].to_list()
                if self.verbose:
                    print(bin_by_cols)
                
                screen = X[~X['grouped']].groupby(bin_by_cols).agg({'wght':['sum']})
                    
                screen = (screen >= self.min_bin)
                screen.columns = screen.columns.droplevel(0)
                
                X = pd.merge(X, screen, how='left', left_on=bin_by_cols,right_index=True)
                X['sum'] = X['sum'].fillna(True)
                # update grouped and group
                X['group'] = np.where((~X['grouped']) & (X['sum']),
                                      X[bin_by_cols].astype(str).agg('\b'.join,axis=1), X['group'])
                X['grouped'] = X['grouped'] | X['sum']
                X = X.drop('sum', axis=1) 
                
            # group ungroupables
            X.loc[X['group']=="",'group'] = "ungrouped"
            
            # converts from observations to group descriptions
            X = X[[choice] + ['group', 'wght']].pivot_table(index='group', columns=choice, aggfunc='sum', fill_value=0)
            
            #convert from counts to shares
            X['rowsum'] = X.sum(axis=1)
            for x in X.columns:
                X[x] = X[x] / X['rowsum']
            X = X.drop('rowsum', axis=1)
            X.columns = [col[1] for col in X.columns]
            X= X.reset_index()
            
            self.coef_ = X
    
    def predict(self, cd):
        """
        Use Estimated model to predict individual choice

        Parameters
        ----------
        cd : pymanda.ChoiceData
            ChoiceData to be predicted on.

        Returns
        -------
        choice_probs : pandas.core.frame.DataFrame
            Dataframe of predictions for each choice.
            When solver ='semiparametric', each row contains probabilities of 
            going to any of the choices.

        """
        # if type(cd) !=  pymanda.ChoiceData:
        #     raise TypeError ('''Expected type pymanda.choices.ChoiceData Got {}'''.format(type(cd)))

        self.check_is_fitted()
        
        if self.solver == 'semiparametric':
            
            #group based on groups
            X = cd.data[self.coef_order].copy()
            X['group'] = ""
            for n in range(len(self.coef_order)):
                X['g'] = X[self.coef_order[:len(self.coef_order) - n]].astype(str).agg('\b'.join,axis=1)
                X['group'] = np.where((X['g'].isin(self.coef_['group'])) & (X['group'] == ""),
                                      X['g'],
                                      X['group'])
            
            X.loc[X['group']=="",'group'] = "ungrouped"
            X = X['group']
            
            choice_probs = pd.merge(X, self.coef_, how='left', on='group')
            choice_probs = choice_probs.drop(columns=['group'])            
            
        
        return choice_probs

    def diversion(self, cd, choice_probs, div_choices, div_choices_var=None):
        '''
        Calculate diversions given a DataFrame of observations with diversion
        probabilities

        Parameters
        ----------
        cd: pymanda.ChoiceData
            ChoiceData to calculate diversions on.

        choice_probs : pandas.core.frame.DataFrame
            DataFrame of observations with diversion probabilities.
            
        div_choices : list
            list of choices to calculate diversions for.
            
        div_choice_var: str
            column name to look for div_choices. If None, will look in 
            cd.corp_var. Default is None

        Returns
        -------
        div_shares : pandas.core.frame.DataFrame
            Columns are name of choice being diverted, 
            rows are shares of diversion.

        '''
        # if type(cd) !=  pymanda.ChoiceData:
        #     raise TypeError ('''Expected type pymanda.choices.ChoiceData Got {}'''.format(type(cd)))
        
        if type(div_choices) != list and div_choices is not None:
            raise TypeError('''choices is expected to be list. Got {}'''.format(type(div_choices)))
        if len(div_choices) == 0:
            raise ValueError ('''choices must have atleast a length of 1''')
            
        if type(choice_probs) != pd.core.frame.DataFrame:
            raise TypeError ('''Expected Type pandas.core.frame.DataFrame. Got {}'''.format(type(choice_probs)))
        
        if div_choices_var is None:
            choice = cd.choice_var
            if cd.corp_var != cd.choice_var:
                corp_map = cd.corp_map()
        elif div_choices_var not in cd.data.columns:
            raise KeyError("""div_choices_var not in cd.data""")
        else:
            choice = div_choices_var
                    
        if len(choice_probs) != len(cd.data):
            raise ValueError('''length of choice_probs and cd.data should be the same''')
            
        choice_probs['choice'] = cd.data[choice]
        
        all_choices = list(choice_probs['choice'].unique())
            
        for c in all_choices:
            if c not in choice_probs.columns:
                raise KeyError ('''{} is not a column in choice_probs'''.format(c))
        
        if cd.wght_var is not None:
            choice_probs['wght'] = cd.data[cd.wght_var]
        else:
            choice_probs['wght'] = 1
        
        div_shares = pd.DataFrame(index=all_choices)
        for diversion in div_choices:
            if div_choices_var is None and cd.corp_var != cd.choice_var:
                div_list = list(corp_map[corp_map[cd.corp_var].isin([diversion])][cd.choice_var])
            else:
                div_list = [diversion]
                
            df = choice_probs[choice_probs['choice'].isin(div_list)].copy()
            
            all_choice_temp = all_choices.copy()
            all_choice_temp = [x for x in all_choice_temp if x not in div_list]
            
            df = df[all_choice_temp + ['wght']]
            df['rowsum'] = df[all_choice_temp].sum(axis=1)
            for x in all_choice_temp:
                df[x] = df[x] / df['rowsum'] * df['wght']
            df = df.drop(columns=['rowsum', 'wght'])
            df = df.sum()
            df = df / df.sum()

            df.name = diversion
            div_shares = div_shares.merge(df, how='left', left_index=True, right_index=True)    
        
        return div_shares
    
    def _export(self, file_path, output_type, output, sheet_name=None):
        """
        Utility function for exporting data.
        """
        accepted_types  = ["csv", "excel"]
        if output_type not in accepted_types:
            raise KeyError("{input} is not a supported format. Valid export options are {list}".format(input=output_type, list=accepted_types))
           
        if output_type == "csv":
            output.to_csv(file_path)
        
        elif output_type == "excel":
            try:
                with pd.ExcelWriter(file_path, mode="a", engine="openpyxl") as writer:
                    try:
                        workbook = writer.book
                        workbook.remove(workbook[sheet_name])
                    except KeyError:
                        pass
                    finally:    
                        output.to_excel(writer, sheet_name=sheet_name, index=False)
            except FileNotFoundError:
                with pd.ExcelWriter(file_path, mode="w", engine="openpyxl") as writer:
                        output.to_excel(writer, sheet_name=sheet_name, index=False)
                 
    def export_diversions(self, div_shares, cd, export=True, output_type="excel", file_path=None, sheet_name="Diversions"):
        """
        Formatting options for diversions() output

        Parameters
        ----------
        div_shares : pandas.core.frame.DataFrame
            Output from ChoiceData.diversions().
        export : Bool, optional
            Boolean to export data. The default is True.
        output_type : string, optional
            Export file format. The default is "excel".
        file_path : string, optional
            Destination to export files. The default is None.

        """
        if type(export) != bool:
            raise ValueError("Export parameter must be type bool")
            
        if output_type =="csv" and len(div_shares.columns)>1:
            raise KeyError("Output type 'csv' is not supported for multiple share tables. Use output_type='excel'.")
    
        divs = list(div_shares.columns)
        choices = list(div_shares.index) 
        
        final_out = {}
        for div in divs:
            base_df = div_shares[[div]].copy()
            
            if div not in choices or self._used_corp:
                if cd.wght_var is None:
                    diverted = len(cd.data[cd.data[cd.corp_var]==div])
                else:
                    diverted = cd.data[cd.data[cd.corp_var]==div].sum(cd.wght_var)
            else:
                if cd.wght_var is None:
                    diverted = len(cd.data[cd.data[cd.choice_var]==div])
                else:
                    diverted = cd.data[cd.data[cd.choice_var]==div].sum(cd.wght_var)

                
            base_df[div + "_diverted"] = base_df[div] * diverted
            base_df = base_df.reset_index().rename(columns={"index": cd.choice_var})
            
            #add base shares
            base_share = cd.calculate_shares()
            base_share = cd.export_shares(base_share, export=False)
            base_share = base_share['Base Shares']
            
            
            # add subtotals
            if cd.corp_var != cd.choice_var:
                corp_map = cd.corp_map()
                base_df = corp_map.merge(base_df, on=cd.choice_var)
                                
                corp_shares = base_df.groupby(cd.corp_var).sum().reset_index()
                corp_shares[cd.choice_var] = "AAAAA"
                base_df = base_df.append(corp_shares)
                
                sort_col = corp_shares.columns[-2]
                corp_sort = corp_shares[[cd.corp_var, sort_col]] # sort on highest threshold
                corp_sort = corp_sort.rename(columns={sort_col: "subtotal sorter"})
                base_df = base_df.merge(corp_sort, how='left', on=cd.corp_var)
                
                base_df = base_df.fillna(0)
                
                base_df.sort_values(['subtotal sorter',  cd.corp_var, sort_col, cd.choice_var], ascending=[False, True, False, True], inplace= True)
                base_df = base_df.drop(columns="subtotal sorter")
                base_df[cd.choice_var] = base_df[cd.choice_var].str.replace("AAAAA", "Total")
                
                id_cols= [cd.corp_var, cd.choice_var]
                
            else:
                sort_col = base_df.columns[-1]
                base_df = base_df.sort_values(sort_col, ascending=False)
                
                id_cols = [cd.choice_var]
                
            base_df = base_df.reset_index(drop=True)
            

            # add a total row
            sums = pd.DataFrame({"totals": base_df.sum()})
            sums = sums.T
            sums = sums.drop(columns=id_cols)
            
            if cd.corp_var != cd.choice_var:
                sums = sums / 2

            num_cols = list(sums.columns)
            for col in id_cols:
                sums[col]= "Total"
            sums = sums[id_cols + num_cols]
            
            base_df = sums.append(base_df)
            
            rowcheck = base_df[base_df.columns[list(~base_df.columns.isin(id_cols))]]
            
            base_df = base_df[rowcheck.sum(axis=1) != 0]
            base_df = base_df.reset_index(drop=True)
            
            base_df = base_share.merge(base_df, how="right", on=id_cols)
            
            final_out.update({div: base_df})
                 
        if export:
            for key in final_out.keys():
                output = final_out[key]
                self._export(file_path, output_type, output, sheet_name=key)
        else:
            return final_out        
        
    def wtp_change(self, cd, choice_probs, trans_dict):
        """
        Calculate the change in Willingness to Pay (WTP) for a combined entity
        given a DataFrame of predictions

        Parameters
        ----------
        cd: pymanda.ChoiceData
            ChoiceData corresponding to choice_probs.
        choice_probs : pandas.core.frame.DataFrame
            DataFrame of observations with diversion probabilities 
            corresponding to cd.
        trans_list: dict
            Dict of lists of choices to calculate WTP change on.

        Returns
        -------
        wtp_df : pandas.core.frame.DataFrame
            1 row dataframe with columns showing individual WTP of elements 
            in trans_list and wtp of a combined entity

        """
        
        if type(trans_dict) != dict:
            raise TypeError ('''trans_dict expected type dict. got {}'''.format(type(trans_dict)))
        
        for key in trans_dict.keys():
            trans_list = trans_dict[key]
            if type(trans_list) != list:
                raise TypeError ('''trans_list expected type list. got {}'''.format(type(trans_list)))    
                
            if len(trans_list) < 2:
                raise ValueError ('''trans_list needs atleast 2 choices''')
            
            for tran in trans_list:
                if tran not in choice_probs.columns:
                    raise KeyError ('''{} is not a choice in choice_probs'''.format(tran))

        final_output = {}
        for key in trans_dict.keys():
            trans_list = trans_dict[key]
            wtp_df = choice_probs[trans_list].copy()
            
            wtp_df['combined'] = wtp_df.sum(axis=1)
            
    
            if (wtp_df==1).any().any():
                warnings.warn('''A diversion probability for a bin equals 1 which will result in infinite WTP.''' , RuntimeWarning)
            
            with warnings.catch_warnings(record = True): # prevents redundant warning for np.log(0)
                wtp_df = -1 * np.log(1- wtp_df) # -1 * ln(1-prob)
            
            if cd.wght_var is not None:
                cols = wtp_df.columns
                wtp_df['wght'] = cd.data[cd.wght_var]
                for c in cols:
                    wtp_df[c] = wtp_df[c] * wtp_df['wght']
                wtp_df = wtp_df.drop(columns=['wght'])
                
            wtp_df = wtp_df.sum().to_frame().transpose()
            
            wtp_df['wtp_change'] = (wtp_df['combined'] - wtp_df[trans_list].sum(axis = 1)) /  wtp_df[trans_list].sum(axis = 1)
        
            final_output.update({key: wtp_df})
            
        return final_output   

    def export_wtp(self, wtp_changes, cd=None, export=True, output_type="excel", file_path=None, sheet_name="wtp changes"):
        if type(export) != bool:
            raise ValueError("Export parameter must be type bool")
                    
        if export:
            for key in wtp_changes.keys():
                out = wtp_changes[key]
                out = out.T
                out = out.reset_index()
                out.columns = ["Entity", "WTP"]
                self._export(file_path, output_type, out, sheet_name=key)
        else:
            return wtp_changes        
        
        
    def upp(self, cd, upp_dict1, upp_dict2, div_shares):
        """
        Calculate Upward Pricing Pressure (UPP)  using estimated diversions for
        2 choices

        Parameters
        ----------
        cd : pymanda.ChoiceData
            ChoiceData corresponding to div_shares.
        upp_dict1 : dict
            Dictionary containing data for necessary UPP calculations.
                'name': name of choice. Always looks at cd.corp_var
                'price': Average corp price
                'margin': Corp margins
        upp_dict2 : dict
            Dictionary containing data for necessary UPP calculations.
                'name': name of choice. Always looks at cd.corp_var
                'price': Average corp price
                'margin': Corp margins
        div_shares : pandas.core.frame.DataFrame
            Diversion shares for choices in upp_dict.

        Returns
        -------
        upp : pandas.core.frame.DataFrame
            Dataframe showing the UPP for each choice and average upp.

        """
        # if type(cd) !=  pymanda.ChoiceData:
        #     raise TypeError ('''Expected type pymanda.choices.ChoiceData Got {}'''.format(type(cd)))
        
        expected_keys = ['name', 'price', 'margin']
        msg = '''upp_dict is expected to have only the following keys: {}'''.format(expected_keys)
        for d in [upp_dict1, upp_dict2]:
            if type(d) != dict:
                raise TypeError('''upp_dict is expected to be type dict. Got {}'''.format(type(d)))
            
            if len(d.keys()) != len(expected_keys):
                raise ValueError(msg)
            for key in d.keys():
                if key not in expected_keys:
                    raise KeyError(msg)
            
                if d['name'] not in list(cd.data[cd.corp_var]):
                    raise KeyError('''{name} is not a choice in ChoiceData column {col}'''.format(name=d['name'], col=cd.data[cd.corp_var]))
                              
                if type(d['price']) not in [int, float]:
                    raise TypeError(''' 'price' is expected to be numeric. Got {}'''.format(type(d['price'])))
                
                if type(d['margin']) not in [int, float]:
                    raise TypeError(''' 'margin' is expected to be numeric. Got {}'''.format(type(d['margin'])))
        
        if type(div_shares) != pd.core.frame.DataFrame:
            raise TypeError('''div_shares expected to be type pandas.core.frame.DataFrame. Got {}'''.format(type(div_shares)))
        
        if cd.corp_var != cd.choice_var:
            corp_map = cd.corp_map()
            index_keep1 = list(corp_map[corp_map[cd.corp_var] == upp_dict1['name']]['choice'])
            index_keep2 = list(corp_map[corp_map[cd.corp_var] == upp_dict2['name']]['choice'])
        else:
            index_keep1 = [upp_dict1['name']]
            index_keep2 = [upp_dict2['name']]

        div1_to_2 = div_shares[upp_dict1['name']][div_shares.index.isin(index_keep2)].sum()
        div2_to_1 = div_shares[upp_dict2['name']][div_shares.index.isin(index_keep1)].sum()
        
        upp1 = div1_to_2 * upp_dict2['margin'] * upp_dict2['price'] / upp_dict1['price']
        upp2 = div2_to_1 * upp_dict1['margin'] * upp_dict1['price'] / upp_dict2['price']        
        
        if cd.wght_var is not None:
            obs1 = cd.data[cd.wght_var][cd.data[cd.corp_var] == upp_dict1['name']].sum()
            obs2 = cd.data[cd.wght_var][cd.data[cd.corp_var] == upp_dict2['name']].sum()
        else:
            obs1 = cd.data[cd.corp_var][cd.data[cd.corp_var] == upp_dict1['name']].count()
            obs2 = cd.data[cd.corp_var][cd.data[cd.corp_var] == upp_dict2['name']].count()
            
        avg_upp = (upp1 * obs1  + upp2 * obs2) / (obs1 + obs2)
        
        upp = pd.DataFrame({'upp_{}'.format(upp_dict1['name']): upp1,
                            'upp_{}'.format(upp_dict2['name']): upp2,
                            'avg_upp': avg_upp}, index = [0])
        
        return upp

    def export_upp(self, upp, cd=None, export=True, output_type="excel", file_path=None, sheet_name="UPP"):
        if type(export) != bool:
            raise ValueError("Export parameter must be type bool")
        out = upp
        out = out.T
        out = out.reset_index()
        out.columns = ["Entity", "UPP"]
        if export:
            self._export(file_path, output_type, out, sheet_name=sheet_name)
        else:
            return out    