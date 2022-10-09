###################################################
##### RAD-seq - Red Sea - Pocilloporid corals #####
###################################################

##### 07c Split individuals by genetic cluster - Stylophora pistillata #####

#### 07c.01. 
# split indivduals according with the ADMIXTURE inferred cluster - Stylophora pistillata

# Libraries
library(dplyr)
library(scales)

# Working directory K6
setwd("~/RADseq/Genotyping/Spis/p1_mac4_r80_448samples/spis_individuals_split_by_cluster_20210302/K6")

# K=6 => pong representative run run9_allmarkers_cv10_K6 (this result is supported by 2 runs that converge to the same answer with an average similarity of 99.9%)

# color used in pong 
pong.col <- c("#1E90FF", "#32CD32", "#FFD700", "#FE92CD", "#C71585", "#FF4500", "#A5AEB4", "#FD9202", "#FFFAF0", "#7B68EE", "#000000") 


# Read the ancestry memebership matrix
#ln -s /home/buitracn/RADseq/Genotyping/Spis/p1_mac4_r80_448samples/spis_ADMIXTURE_20210222/Pong_visualization/spis.allmarkers.cv10.r9.indordered.6.Q .
spis.admix.K6.r9.rep <- read.delim("spis.allmarkers.cv10.r9.indordered.6.Q", sep = "", header = F)

colnames(spis.admix.K6.r9.rep) <- paste("SCL", seq(1:6), sep = "") # bear in mind the match between color and column number

# ln -s /home/buitracn/RADseq-Big-project/spis/p1_mac4_r80_448samples/04_ADMIXTURE_20210222/Pong_visualization/spis.ind.ordered.byclusters.txt .
spis.id.ordered <- read.delim("spis.ind.ordered.byclusters.txt", header = F)
rownames(spis.admix.K6.r9.rep) <- spis.id.ordered$V1

spis.genclust <- mutate(spis.admix.K6.r9.rep, major.clust = case_when(SCL1 >= 0.9 ~ "SCL1",
                                                                      SCL2 >= 0.9 ~ "SCL2",
                                                                      SCL3 >= 0.9 ~ "CSL3",
                                                                      SCL4 >= 0.9 ~ "SCL4",
                                                                      SCL5 >= 0.9 ~ "SCL5",
                                                                      SCL6 >= 0.9 ~ "SCL6",
                                                                      TRUE ~ "Admix"))

spis.clustersID <- paste("SCL", seq(1:6), sep = "" )
for (i in spis.clustersID){
  cluster <- rownames(subset(spis.genclust, major.clust == i))
  write.table(cluster, paste(i,".txt", sep = ""), quote = F, col.names = F, row.names = F)
}

table(spis.genclust$major.clust)
# Admix   CL1   CL2   CL3   CL4   CL5   CL6 
#   55    47    50    51    71    34    59 

# Within the group classified as admixed individuals (more than 10% of a secundary cluster) there are SKAU-R2=4, SDOG-R1=7, SFAR-R1=3, SFAR-R2=7, SFAR-R3=5, SFAR-R4=4
# spis.genclust[grep("Admix", spis.genclust$major.clust), ]

# create strata with the new clusters
spis.genclust.strata <- data.frame(INDIVIDUALS = rownames(spis.genclust),
                                   STRATA = spis.genclust$major.clust) 
spis.genclust.strata <- spis.genclust.strata[ grep("Admix", spis.genclust.strata$STRATA, invert = TRUE) , ] #312 individuals

write.table(spis.genclust.strata, file = "spis.genclust.strata.K6.tsv", sep = "\t", quote = F, row.names = F)

