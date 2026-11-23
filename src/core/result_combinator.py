import os
import json
import csv
import re

import os
import json
import csv
import re

def combine_results(directory_path):
    all_data = []
    article_count = 0

    for filename in os.listdir(directory_path):
        if filename.endswith('_extracted.json'):
            file_path = os.path.join(directory_path, filename)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                article_count += 1
                result_filename = os.path.join(directory_path, f'article_{article_count}_summarization.md')
                
                # Write final results to separate text file
                with open(result_filename, 'w', encoding='utf-8') as result_file:
                    result_file.write(data['summarization'])
                
                row = {
                    'title': data['title'],
                    **data['final_results']
                }
                
                all_data.append(row)

    # Write to CSV
    if all_data:
        keys = all_data[0].keys()
        output_file = os.path.join(directory_path, f'combined_summary.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys, quoting=csv.QUOTE_ALL)
            dict_writer.writeheader()
            dict_writer.writerows(all_data)
        print(f"Combined results have been written to {output_file}")
        print(f"Individual result files have been created for {article_count} articles")
    else:
        print("No data found to combine.")

# def extract_sample_size(population_characteristics):
#     # Try to extract sample size from the population characteristics
#     match = re.search(r'(?i)sample size.*?(\d+)', population_characteristics)
#     return match.group(1) if match else "Not specified"

# def parse_final_results(final_results):
#     # This function should be adapted based on the expected structure of your final results
#     # For this example, we'll assume a simple key-value pair structure
#     parsed_results = {}
#     lines = final_results.split('\n')
#     for line in lines:
#         if ':' in line:
#             key, value = line.split(':', 1)
#             parsed_results[key.strip()] = value.strip()
#     return parsed_results
