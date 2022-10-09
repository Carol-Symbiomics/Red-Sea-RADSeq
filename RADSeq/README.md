# Buitrago et al., 2022 RAD-Seq data analysis

This directory contains the scripts used to run analyses and produce figures for the RAD-Seq data.

## Workflow
1. Processing of raw sequencing data (00_preprocessing.sh)


### Stylophora pistillata
2. Reference genome RADseq genotyping and filtering of VCF files (01_Spis_RADfiltering.sh)
3. Preliminary relatedness analysis using Identity-By-Descent and visualization (02_Spis_SNPRelate.R)
4. Analysis of Molecular Variance - AMOVA (03_Spis_AMOVA.R)
5. Pairwise FST analysis (04_Spis_PairwiseFST.R)
6. Isolation by distance analysis (05_Spis_IBD.R)
7. Principal component analysis and visualization (06_Spis_PCAstructure.R)
8. Admixture analysis and visualization (07a_Spis_ADMIXTURE.sh; 07b_Spis_ADMIXTUREvisualization.R)
9. Splitting individuals by genetic cluster excluding admixed individuals (07c_Spis_SplittedbyCluster.R)
10. Linkage Disequilibrium (LD) analysis and visualization of LD decay (08a_Spis_LDanalysis.sh; 08b_Spis_LDvisualization.R)
11. Candidate SNPs for positive selection analyses and visualization (09a_Spis_CandidateSNPs_FormatingFiles.R; 09b_Spis_CandidateSNPs_BAYPASS.R; 09c_Spis_CandidateSNPs_BAYESCAN.R; 09d_Spis_CandidateSNPs_visualization.R)

### Pocillopora verrucosa
7. xxx
8. xxx
