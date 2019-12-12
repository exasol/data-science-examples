import pandas as pd
from numpy import array, dtype

class OutputPostprocessor():
    def make_output_descriptions(self, config, input_columns):
        outputs = config["columns"]["output"]
        output_columns = [column
                          for column in input_columns
                          if column.name in outputs]
        output_descriptions = []
        i = 0
        for column in output_columns:
            column_config = outputs[column.name]
            if column_config["type"] == "categorical" and column_config["method"] == "vocabulary":
                output_descriptions.append([column.name, column_config["type"] + column_config["method"],
                                            "keras_output", column.name + "_keras_output", "DOUBLE"])
                output_descriptions.append([column.name, column_config["type"] + column_config["method"],
                                            "max_categories", column.name + "_max_categories", column.sql_type])
                output_descriptions.append([column.name, column_config["type"] + column_config["method"],
                                            "max_probabilities", column.name + "_max_probabilities", "DOUBLE"])

            if column_config["type"] == "categorical" and column_config["method"] == "hash":
                output_descriptions.append([column.name, column_config["type"] + column_config["method"],
                                            "keras_output", column.name + "_keras_output", "DOUBLE"])
            elif column_config["type"] != "categorical":
                output_descriptions.append([column.name, column_config["type"], "keras_output",
                                            column.name + "_keras_output", "DOUBLE"])
        return output_descriptions, output_columns

    def flatten(self, input):
        out = []
        for j in input:
            out.append(*j)
        out_array = array(out, dtype="float32")
        return out_array

    # if you change this function you have to adjust select_outputs_for_default_output_columns
    def select_outputs(self, output, output_descriptions):
        new_output = []
        column_names = []
        for i in range(len(output)):
            output_description = output_descriptions[i]
            if 'categoricalvocabulary' in output_description:
                if 'max_probabilities' in output_description or 'max_categories' in output_description:
                    new_output.append(output[i])
                    column_names.append(output_description[3])
                else:
                    pass
            elif "float" in output_description:
                out_array = self.flatten(output[i])
                new_output.append(out_array)
                column_names.append(output_description[3])
            else:
                raise Exception("Unsupported Type")
                # new_output.append(output[i])
                # column_names.append(output_description[3])

        zipped_output = list(zip(*new_output))
        df = pd.DataFrame.from_records(zipped_output, columns=column_names)
        return df

    # if you change this function you have to adjust select_outputs
    def select_outputs_for_default_output_columns(self, output_descriptions):
        new_output_descriptions = []
        for column in output_descriptions:
            if 'categoricalvocabulary' in column:
                if 'max_probabilities' in column or 'max_categories' in column:
                    new_output_descriptions.append(column)
                else:
                    pass
            else:
                new_output_descriptions.append(column)
        return new_output_descriptions