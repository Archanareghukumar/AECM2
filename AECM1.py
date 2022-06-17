from nis import match
from pkgutil import get_data
import pandas as pd
import sys
import re
import warnings
warnings.filterwarnings('ignore')
from base import BaseSDQApi
import utils as utils
import traceback
import tqdm
import logging
import numpy as np
import yaml
import os
from datetime import datetime


class AECM1(BaseSDQApi):
    domain_list = ['AE', 'CM']
    def execute(self):
        study = self.study_id
        sub_cat = 'AECM1'
        fields_dict = self.get_field_dict(subcat=sub_cat)
        fields_labels = dict(self.get_field_labels(subcat=sub_cat))
        fn_config = self.get_fn_config(study=study, subcat=sub_cat)
        match_config = fn_config['match']
        subjects = self.get_subjects(study, domain_list = self.domain_list, per_page = 10000)
        # deeplink_template = self.get_deeplink(study)
        for subject in tqdm.tqdm(subjects):
            try:
                flatten_data = self.get_flatten_data(study, subject, per_page=10000, domain_list = self.domain_list)
                ae_df = pd.DataFrame(flatten_data['AE'])
                cm_df = pd.DataFrame(flatten_data['CM'])
                #print(ae_df.shape)
                #print(cm_df.shape)
                #print(ae_df[['form_ix', 'AESTDAT']])
                
                for ind in range(ae_df.shape[0]):
                    try:
                        ae_record = ae_df.iloc[[ind]]
                        formindex = ae_record['form_index'].values[0]
                        o_aespid = ae_record['form_ix'].values[0]
                        
                        match_flag, cm_match_df = utils.ae_cm_mapper(prim_rec=ae_record,
                                                           sec_df=cm_df,
                                                           subcat=sub_cat,
                                                           **match_config)
                        if (match_flag is True): 
                            if len(cm_match_df) > 0:      
                                for cm_ind in range(len(cm_match_df)):
                                        #ae_record, cm_rec = utils.get_cm_hierarchy(ae_record, ae_df, cm_record, key = 'AESTDAT')
                                        cm_rec = cm_match_df.iloc[[cm_ind]]
                                        # for aeptcd in ae_record['AETERM'].unique().tolist():
                                        #     new_ae_record = ae_record[ae_record['AETERM'] == aeptcd]
                                        #     if len(new_ae_record) > 1:
                                        #         print('-=>.',new_ae_record.shape, new_ae_record.index.tolist())
                                        #         new_ae_record = new_ae_record.head(1)
                                        new_ae_record = ae_record                                                                                
                                        aespid = new_ae_record['form_ix'].values[0]
                                        new_ae_record1 = new_ae_record

                                        if aespid != o_aespid:
                                            continue
                                            
                                        if type(new_ae_record) != int:
                                            new_ae_record['AESTDAT'] = new_ae_record['AESTDAT'].apply(utils.get_date)
                                            cm_rec['CMSTDAT'] = cm_rec['CMSTDAT'].apply(utils.get_date)
                                            ae_stdt = new_ae_record['AESTDAT'].values[0]
                                            cm_stdt = cm_rec['CMSTDAT'].values[0]
                                            cm_endt = cm_rec['CMENDAT'].values[0]
                                            aecmgiv = new_ae_record['AECONTRT'].values[0].upper()
                                            print(f"CMSTDAT - {cm_stdt}, AESTDAT - {ae_stdt}, AECMGIV - {aecmgiv}")
                                            if not ((str(cm_endt) not in ['','nan','None','NaT'] and cm_endt > ae_stdt) or (str(cm_endt) in ['','nan','None','NaT'])):
                                                continue
                                            if (cm_stdt < ae_stdt) & \
                                                (aecmgiv == 'YES'):   
                                                subcate_report_dict = {}
                                                report_dict = {}
                                                

                                                # new_ae_record1['AESTDAT']= new_ae_record1['AESTDAT'].dt.strftime("%d-%b-%Y")
                                                # cm_rec['CMSTDAT'] = cm_rec['CMSTDAT'].dt.strftime("%d-%b-%Y")

                                                # new_ae_record1['AESTDAT'] = new_ae_record1['AESTDAT'].dt.strftime("%d-%b-%Y")
                                                # cm_rec['CMSTDAT'] = cm_rec['CMSTDAT'].dt.strftime("%d-%b-%Y")
                                                # try:
                                                #     new_ae_record1['AEENDAT'] = new_ae_record1['AEENDAT'].apply(utils.format_datetime)
                                                #     cm_rec['CMENDAT'] = cm_rec['CMENDAT'].apply(utils.format_datetime)
                                                # except:
                                                #     new_ae_record1['AEENDAT'] = utils.format_datetime(new_ae_record1['AEENDAT'])
                                                #     cm_rec['CMENDAT'] = utils.format_datetime(cm_rec['CMENDAT'])

                                                try:
                                                    new_ae_record1['AESTDAT'] = new_ae_record1['AESTDAT'].apply(utils.format_datetime)
                                                    cm_rec['CMSTDAT'] = cm_rec['CMSTDAT'].apply(utils.format_datetime)
                                                except:
                                                    new_ae_record1['AESTDAT'] = utils.format_datetime(new_ae_record1['AESTDAT'])
                                                    cm_rec['CMSTDAT'] = utils.format_datetime(cm_rec['CMSTDAT'])
                                                try:
                                                    new_ae_record1['AEENDAT'] = new_ae_record1['AEENDAT'].apply(utils.format_datetime)
                                                    cm_rec['CMENDAT'] = cm_rec['CMENDAT'].apply(utils.format_datetime)
                                                except:
                                                    new_ae_record1['AEENDAT'] = utils.format_datetime(new_ae_record1['AEENDAT'])
                                                    cm_rec['CMENDAT'] = utils.format_datetime(cm_rec['CMENDAT'])

                                                piv_rec = {'AE' : new_ae_record1.head(1),
                                                            'CM' : cm_rec.head(1)}

                                                ae_record['AESTDAT'] = ae_record['AESTDAT_RAW']
                                                ae_record['AEENDAT'] = ae_record['AEENDAT_RAW']
                                                cm_rec['CMSTDAT'] = cm_rec['CMSTDAT_RAW']
                                                cm_rec['CMENDAT'] = cm_rec['CMENDAT_RAW']
                                                aestdat = ae_record['AESTDAT']
                                                aeendat = ae_record['AEENDAT']
                                                cmstdat = cm_rec['CMSTDAT']
                                                cmendat = cm_rec['CMENDAT']

                                                for dom, cols in fields_dict.items():
                                                    piv_df = piv_rec[dom]

                                                    present_col = [col for col in cols if col in piv_df.columns.tolist()]
                                                    rep_df = piv_df[present_col]
                                                    rep_df['deeplink'] = '#'#utils.get_deeplink(deeplink_template, piv_df)
                                                    rep_df = rep_df.rename(columns=fields_labels)
                                                    report_dict[dom]= rep_df.to_json(orient= 'records')

                                                subcate_report_dict[sub_cat] =  report_dict

                                                aeterm = new_ae_record['AETERM'].values[0]
                                                formidx = cm_rec['form_ix'].values[0]
                                                cmtrt = cm_rec['CMTRT'].values[0]
                                                ae_stdt = new_ae_record1['AESTDAT'].values[0]
                                                cm_stdt = cm_rec['CMSTDAT'].values[0]

                                                ae_record1 = new_ae_record1.head(1).squeeze()

                                                query_text_param = {
                                                                    'CM_FORMIDX':formidx, 
                                                                    'CMTRT':cmtrt, 
                                                                    'AESPID':aespid, 
                                                                    'AETERM':aeterm, 
                                                                    'CMSTDAT':cm_stdt, 
                                                                    'AESTDAT':new_ae_record1['AESTDAT'].values[0],
                                                                    'CMREFID':formidx
                                                                    }
                                                payload = {
                                                    "subcategory": sub_cat,
                                                    "query_text": self.get_model_query_text_json(study, sub_cat, params = query_text_param),
                                                    "form_index": str(ae_record1['form_index']),
                                                    "question_present": self.get_subcategory_json(study, sub_cat),
                                                    "modif_dts": str(ae_record1['modif_dts']),  
                                                    "stg_ck_event_id": int(ae_record1['ck_event_id']),
                                                    "formrefname" : str(ae_record1['formrefname']),
                                                    "report" : subcate_report_dict,
                                                    "confid_score": np.random.uniform(0.7, 0.97)
                                                }
                                                print('payload-recon->formix,AESPID',new_ae_record1['form_ix'].values[0],new_ae_record1['AESPID'].values[0],payload)
                                                self.insert_query(study, subject, payload)
                                                print(payload)
                                                #break
                            
                    except:
                        print(traceback.format_exc())
                        continue       

            except Exception as e:
                print(traceback.format_exc())
                logging.exception(e)
                                                
if __name__ == '__main__':
    study_id = sys.argv[1]
    rule_id = sys.argv[2]
    version = sys.argv[3]
    rule = AECM1(study_id, rule_id, version)
    rule.run()
