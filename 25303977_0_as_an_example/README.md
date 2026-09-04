# Task description

for each patient, calculate the frequency of mutations in terms of: A->C, A->G, A->T, C->A, C->G, C->T, CC->TT.  `->` indicates the substitution mutation. The patterns can be found by comparing reference allele and sequencing results of allele of the tumor sample. Save the results as pd.DataFrame named `substitution_ratios`, its format should be like

| Tumor_Sample_Barcode   |        A>C |       A>G |       A>T |       C>A |        C>G |      C>T |     CC>TT |   Others |
|:-----------------------|-----------:|----------:|----------:|----------:|-----------:|---------:|----------:|---------:|
| CSCC-1-T               | 0.0077821  | 0.0389105 | 0.0311284 | 0.167315  | 0.0311284  | 0.163424 | 0         | 0.560311 |
| CSCC-10-T              | 0.00854473 | 0.0149533 | 0.0136182 | 0.0154873 | 0.00774366 | 0.401335 | 0.0259012 | 0.512417 |
[... more rows]

# CoT Instructions

1. **Load the Mutation Data**: - Read the mutation data from the CSV file into a pandas DataFrame named `data_mutations`. Ensure that the relevant columns for reference alleles and tumor alleles are included.
 
 2. **Define Substitution Function**: - Create a function named `determine_substitution` that takes two arguments: the reference allele and the tumor allele. This function should determine the type of substitution mutation based on the following rules: 
  - If the reference allele matches the tumor allele, return `None`.
  - If the reference allele is 'A' and the tumor allele is 'C', return 'A>C'.
  - If the reference allele is 'A' and the tumor allele is 'G', return 'A>G'.
  - If the reference allele is 'A' and the tumor allele is 'T', return 'A>T'.
  - If the reference allele is 'C' and the tumor allele is 'A', return 'C>A'.
  - If the reference allele is 'C' and the tumor allele is 'G', return 'C>G'.
  - If the reference allele is 'C' and the tumor allele is 'T', return 'C>T'.
  - If the reference allele is 'C' and the tumor allele is 'C', return 'CC>TT'.
  - For any other combinations, return 'Others'.
 
 3. **Apply Substitution Function**: - Use the `apply` method to apply the `determine_substitution` function to each row of the DataFrame for both tumor alleles (e.g., `Tumor_Seq_Allele1` and `Tumor_Seq_Allele2`). Store the results in new columns named `Substitution1` and `Substitution2`.
 
 4. **Combine Substitutions**: - Create a new column named `Substitution` that combines the results from `Substitution1` and `Substitution2`, ensuring that if one is `None`, the other is used.
 
 5. **Filter Data**: - Remove any rows from `data_mutations` where the `Substitution` column is `None` to focus only on valid substitutions.
 
 6. **Calculate Substitution Ratios**: - Group the DataFrame by `Tumor_Sample_Barcode` and `Substitution`, then count the occurrences of each substitution type. Use the `unstack` method to pivot the DataFrame so that each substitution type becomes a column. Fill any missing values
