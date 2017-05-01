__author__ = 'Ryan Jacobs'

import data_parser
import sys
import os
from MASTMLInitializer import ConfigFileParser, MASTMLWrapper
import logging
import shutil

class MASTMLDriver(object):

    def __init__(self, configfile):
        self.configfile = configfile
        if os.getenv("MAST_DEBUG") == "1":
            logging.basicConfig(filename='MASTMLlog.log', level='DEBUG')
        else:
            logging.basicConfig(filename='MASTMLlog.log', level='INFO')

    def string_or_list_input_to_list(self, unknown_input_val):
        input_list=list()
        if type(unknown_input_val) is str:
            input_list.append(unknown_input_val)
        elif type(unknown_input_val) is list:
            for unknown_input in unknown_input_val:
                input_list.append(unknown_input)
        return input_list

    def run_MASTML(self):
        cwd = os.getcwd()
        config = ConfigFileParser(configfile=self.configfile)
        logging.info('Successfully read in your MASTML input file, %s' % str(self.configfile))

        configdict = config.get_config_dict()
        mastmlwrapper = MASTMLWrapper(configdict=configdict)
        generalsetup = mastmlwrapper.process_config_keyword(keyword='General Setup')
        datasetup = mastmlwrapper.process_config_keyword(keyword='Data Setup')
        models_and_tests_setup = mastmlwrapper.process_config_keyword(keyword='Models and Tests to Run')
        logging.info('Successfully parsed your MASTML input file')
        
        # General setup
        save_path = os.path.abspath(generalsetup['save_path'])
        if not os.path.isdir(save_path):
            os.mkdir(save_path)

        # Temporary call to data_parser for now, but will later deprecate
        data_dict=dict()
        for data_name in datasetup.keys():
            data_path = datasetup[data_name]['data_path']
            data_weights = datasetup[data_name]['weights']
            if not(os.path.isfile(data_path)):
                raise OSError("No file found at %s" % data_path)
            data_dict[data_name] = data_parser.parse(data_path, data_weights)
            #data_dict[data_name].set_x_features(datasetup['X']) #set in test classes, not here, since different tests could have different X and y features
            #data_dict[data_name].set_y_feature(datasetup['y'])
            logging.info('Parsed the input data located under %s' % data_path)

        # Gather models
        model_list = []
        model_val = models_and_tests_setup['models']
        print(model_val)
        if type(model_val) is str:
            logging.info('Getting model %s' % model_val)
            ml_model = mastmlwrapper.get_machinelearning_model(model_type=model_val)
            model_list.append(ml_model)
            logging.info('Adding model %s to queue...' % str(model_val))
        elif type(model_val) is list:
            for model in model_val:
                logging.info('Getting model %s' % model)
                ml_model = mastmlwrapper.get_machinelearning_model(model_type=model)
                model_list.append(ml_model)
                logging.info('Adding model %s to queue...' % str(model))
        # Gather test types
        test_list=self.string_or_list_input_to_list(models_and_tests_setup['test_cases'])
        # Run the specified test cases for every model
        for test_type in test_list:
            logging.info('Looking up parameters for test type %s' % test_type)
            test_params = configdict["Test Parameters"][test_type]
            # Set data lists
            training_dataset_name_list = self.string_or_list_input_to_list(test_params['training_dataset'])
            training_dataset_list = list()
            for dname in training_dataset_name_list:
                training_dataset_list.append(data_dict[dname])
            test_params['training_dataset'] = training_dataset_list
            testing_dataset_name_list = self.string_or_list_input_to_list(test_params['testing_dataset'])
            testing_dataset_list = list()
            for dname in testing_dataset_name_list:
                testing_dataset_list.append(data_dict[dname])
            test_params['testing_dataset'] = testing_dataset_list
            # Run the test case for every model
            for midx, model in enumerate(model_list):
                mastmlwrapper.get_machinelearning_test(test_type=test_type,
                        model=model, save_path=save_path,
                        **test_params)
                logging.info('Ran test %s for your %s model' % (test_type, str(model)))
        # Move input and log files to output directory, end MASTML session
        if not(os.path.abspath(generalsetup['save_path']) == cwd):
            if os.path.exists(generalsetup['save_path']+"/"+'MASTMLlog.log'):
                os.remove(generalsetup['save_path']+"/"+'MASTMLlog.log')
            shutil.move(cwd+"/"+'MASTMLlog.log', generalsetup['save_path'])
            shutil.copy(cwd+"/"+str(self.configfile), generalsetup['save_path'])
        return

if __name__ == '__main__':
    if len(sys.argv) > 1:
        mastml = MASTMLDriver(configfile=sys.argv[1])
        mastml.run_MASTML()
        logging.info('Your MASTML runs are complete!')
    else:
        print('Specify the name of your MASTML input file, such as "mastmlinput.conf", and run as "python AllTests.py mastmlinput.conf" ')

