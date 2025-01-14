#!/usr/bin/env python3

from sputils.spbars import SPBars
from sputils.sphierarchical import SPHierarchical
import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
plt.rcParams['svg.fonttype'] = 'none'
import matplotlib.gridspec as gridspec
import pandas as pd
import os
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from itertools import chain
from matplotlib.colors import ListedColormap
import numpy as np
from collections import defaultdict
import re
import itertools
import pickle
import skbio

class Buitrago:
    """
    A base class that will give access to the basic meta info dfs
    For the plotting of the ordinations and the bar plots
    we only want to be plotting the samples that are in the two lists:
    pver.ind.ordered.byclusters.txt
    spis.ind.ordered.byclusters.txt
    We will get the reef info from the name.
    """
    def __init__(self, dist_type):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.plotting_dir = os.path.join(self.root_dir, "plots")

        # Absolute abundance count table paths
        self.seq_count_table_path = os.path.join(self.root_dir,
                                                 'sp_output/post_med_seqs/131_20201203_DBV_20201207T095144.seqs.absolute.abund_and_meta.txt')
        self.profile_count_table_path = os.path.join(self.root_dir,
                                                     'sp_output/its2_type_profiles/131_20201203_DBV_20201207T095144.profiles.absolute.abund_and_meta.txt')

        # dfs that hold reef and region info
        self.pver_df = self._make_pver_df()

        self.spis_df = self._make_spis_df()

        self.all_samples_df = pd.concat([self.pver_df, self.spis_df])
        self.sample_names = list(self.all_samples_df.index.values)

        # Color dictionaries
        self.regions = ['MAQ', 'WAJ', 'YAN', 'KAU', 'DOG', 'FAR']
        self.region_color_dict = {
            'MAQ': '#222f4f', 'WAJ': '#10788f', 'YAN': "#bdd7c2",
            'KAU': '#e9d88a', 'DOG': '#f0946d', 'FAR': '#bc402a'
        }
        self.species_color_dict = {'P': '#BEBEBE', 'S': '#464646'}
        self.reefs = ['R1', 'R2', 'R3', 'R4']
        self.reef_marker_shape_dict = {'R1': 'o', 'R2': '^', 'R3': 's', 'R4': '+'}

        # Determine the samples for plotting that contain Symbiodinium
        # Run SPHier through blank to get the list of samples we have in the A matrix
        # THen find the interset of samples listed in the self.pver and self.spis dfs.
        if dist_type == 'bc':
            self.symbiodinium_dist_path = 'sp_output/between_sample_distances/A/20201207T095144_braycurtis_sample_distances_A_sqrt.dist'
        elif dist_type == 'uf':
            self.symbiodinium_dist_path = 'sp_output/between_sample_distances/A/20201207T095144_unifrac_sample_distances_A_sqrt.dist'

        self.sph = SPHierarchical(dist_output_path=self.symbiodinium_dist_path, no_plotting=True)
        self.symbiodinium_names = self.sph.obj_name_to_obj_uid_dict.keys()
        self.symbiodinium_host_names = set(self.symbiodinium_names).intersection(set(self.all_samples_df.index))
        self.symbiodinium_sample_uid_to_sample_name_dict = {
            k: v for k, v in self.sph.obj_name_to_obj_uid_dict.items() if k in self.symbiodinium_host_names
        }
        self.symbiodinium_sample_uid_to_sample_name_dict = {
            v: k for k, v in self.symbiodinium_sample_uid_to_sample_name_dict.items()
        }

    def _make_spis_df(self):
        with open("spis.ind.ordered.byclusters.txt", "r") as f:
            spis_to_plot = [_.rstrip() for _ in f]
        spis_df_list = []
        for _ in spis_to_plot:
            # list of sample name, reef, region
            reef = '-'.join(_.split('-')[:2])[1:]
            region = reef.split('-')[0]
            spis_df_list.append([_, reef, region])
        spis_df = pd.DataFrame(spis_df_list, columns=['sample_name', 'reef', 'region'])
        spis_df = spis_df.set_index('sample_name')
        spis_df.drop(labels=['SWAJ-R1-43'], axis=0, inplace=True)
        return spis_df

    def _make_pver_df(self):
        with open("pver.ind.ordered.byclusters.txt", "r") as f:
            pver_to_plot = [_.rstrip() for _ in f]
        pver_df_list = []
        for _ in pver_to_plot:
            # list of sample name, reef, region
            reef = '-'.join(_.split('-')[:2])[1:]
            region = reef.split('-')[0]
            pver_df_list.append([_, reef, region])
        df = pd.DataFrame(pver_df_list, columns=['sample_name', 'reef', 'region'])
        return df.set_index('sample_name')


    def _mm2inch(self, *tupl):
        inch = 25.4
        if isinstance(tupl[0], tuple):
            return tuple(i / inch for i in tupl[0])
        else:
            return tuple(i / inch for i in tupl)


class BuitragoOrdinations(Buitrago):
    """Plot PCoA ordinations. In the end this code was not used and rather the plots were made in R so that they were compatible
    with the 16S plots. See script plot_buitrago.R"""
    # We have the list of Symbiodinium samples that also have related host sample data
    # read in the pcoA coords and keep only the samples that are in
    def __init__(self, dist_type='bc'):
        super().__init__(dist_type=dist_type)
        if dist_type == 'bc':
            self.pcoa_df = pd.read_csv(
                'sp_output/between_sample_distances/A/20201207T095144_braycurtis_samples_PCoA_coords_A_sqrt.csv')
        else:
            self.pcoa_df = pd.read_csv(
                'sp_output/between_sample_distances/A/20201207T095144_unifrac_sample_PCoA_coords_A_sqrt.csv')
        self.pcoa_df.set_index('sample', inplace=True)
        # Plot species wise
        # four components per species
        self.fig, self.ax_arr = plt.subplots(nrows=4, ncols=2, figsize=self._mm2inch(200, 300))
        self.ax_gen = chain.from_iterable(zip(*self.ax_arr))


        # Then Plot up species by ordination
        for species, species_df in zip(['Pocillopra', 'Stylophora'],[self.pver_df, self.spis_df]):
            for pc in ['PC2', 'PC3', 'PC4', 'PC5']:
                ax = next(self.ax_gen)
                for region in self.region_color_dict.keys():
                    for reef in self.reef_marker_shape_dict.keys():

                        #Get the samples that are of the given region, reef and in the symbiodinium host samples
                        plot_df = species_df[
                            (species_df['REGION'] == region) &
                            (species_df['REEF'].str.contains(reef))
                        ]
                        sym_host_plot = [_ for _ in plot_df.index if _ in self.symbiodinium_host_names]
                        plot_df = self.pcoa_df.loc[sym_host_plot, :]
                        edgecolors = None
                        if reef == 'R4':
                            scatter = ax.scatter(
                                x=plot_df['PC1'], y=plot_df[pc],
                                c=self.region_color_dict[region],
                                marker=self.reef_marker_shape_dict[reef], s=10, alpha=0.8
                            )
                        else:
                            scatter = ax.scatter(
                                x=plot_df['PC1'], y=plot_df[pc],
                                c=self.region_color_dict[region],
                                marker=self.reef_marker_shape_dict[reef], s=10, alpha=0.8,
                                edgecolors=edgecolors, linewidths=0
                            )
                        foo = 'bar'
                if pc == 'PC2':
                    import matplotlib.lines as mlines
                    handles = []
                    for region in self.regions:
                        # The region markers
                        handles.append(
                            mlines.Line2D(
                                [], [], color=self.region_color_dict[region],
                                marker='o', markersize=2, label=region, linewidth=0
                            )
                        )
                    for reef in self.reefs:
                        # The reef markers
                        handles.append(
                            mlines.Line2D(
                                [], [], color='black',
                                marker=self.reef_marker_shape_dict[reef],
                                markersize=2, label=reef, linewidth=0
                            )
                        )
                    ax.legend(handles=handles, loc='upper left', fontsize='xx-small')
                    ax.set_title(species, fontsize='x-small')
                ax.set_ylabel(f'{pc} {self.pcoa_df.at["proportion_explained", pc]:.2f}')
                ax.set_xlabel(f'PC1 {self.pcoa_df.at["proportion_explained", "PC1"]:.2f}')
                self._set_lims(ax)
        foo = 'bar'
        plt.tight_layout()
        print('saving .svg')
        plt.savefig(f'{dist_type}_ITS2_ordinations.svg')
        print('saving .png')
        plt.savefig(f'{dist_type}_ITS2_ordinations.png', dpi=1200)
        foo = 'bar'

    def _set_lims(self, ax):
        # Get the longest side and then set the small side to be the same length
        x_len = ax.get_xlim()[1] - ax.get_xlim()[0]
        y_len = ax.get_ylim()[1] - ax.get_ylim()[0]
        if y_len > x_len:
            # Then the y is the longest and we should adust the x to be bigger
            x_mid = ax.get_xlim()[0] + (x_len / 2)
            x_max = x_mid + (y_len / 2)
            x_min = x_mid - (y_len / 2)
            ax.set_xlim(x_min, x_max)
            ax.set_aspect('equal', 'box')
            return
        else:
            # Then the y is the longest and we should adust the x to be bigger
            y_mid = ax.get_ylim()[0] + (y_len / 2)
            y_max = y_mid + (x_len / 2)
            y_min = y_mid - (x_len / 2)
            ax.set_ylim(y_min, y_max)
            ax.set_aspect('equal', 'box')
            return

class BuitragoHier_split_species(Buitrago):
    """
    Plot up a series of dendrograms
    This dendogram will be split by species and we will perform clustering for each species and plot this up as well
    """
    def __init__(self, dist_type='bc', consolidate_profiles=True):
        super().__init__(dist_type=dist_type)

        # setup fig
        # 6 rows for the dendro and 1 for the coloring by species
        gs = gridspec.GridSpec(nrows=19, ncols=2)

        self.fig = plt.figure(figsize=(self._mm2inch(183, 80)))
        self.dendro_ax_spis = plt.subplot(gs[:8, 1:2])
        self.seq_bars_ax_spis = plt.subplot(gs[8:12, 1:2])
        self.prof_bars_ax_spis = plt.subplot(gs[12:16, 1:2])
        self.region_ax_spis = plt.subplot(gs[16:18, 1:2])


        self.dendro_ax_pver = plt.subplot(gs[:8, :1])
        self.seq_bars_ax_pver = plt.subplot(gs[8:12, :1])
        self.prof_bars_ax_pver = plt.subplot(gs[12:16, :1])
        self.region_ax_pver = plt.subplot(gs[16:18, :1])


        self.region_ax_legend = plt.subplot(gs[18:19, :])
        # TODO make an overall braycurtis matrix instead of just symbiodinium and try working with this.
        self.symbiodinium_host_names_spis = [_ for _ in self.symbiodinium_host_names if _[0] == "S"]
        self.sph_spis = SPHierarchical(
            dist_output_path=self.symbiodinium_dist_path, ax=self.dendro_ax_spis,
            sample_names_included=self.symbiodinium_host_names_spis)
        self.sph_spis.plot()
        self.dendro_ax_spis.collections[0].set_linewidth(0.25)
        # self.dendro_ax_spis.set_ylim(0,0.8)
        self.dendro_ax_spis.set_title("S. pistillata", style='italic', fontsize='small')

        self.symbiodinium_host_names_pver = [_ for _ in self.symbiodinium_host_names if _[0] == "P"]
        self.sph_pver = SPHierarchical(
            dist_output_path=self.symbiodinium_dist_path, ax=self.dendro_ax_pver,
            sample_names_included=self.symbiodinium_host_names_pver)
        self.sph_pver.plot()
        self.dendro_ax_pver.collections[0].set_linewidth(0.25)
        # self.dendro_ax_pver.set_ylim(0, 0.8)
        self.dendro_ax_pver.set_title("P. verrucosa", style='italic', fontsize='small')

        # We will hardcode the x coordinates as they seem to be standard for the dendrogram plots
        self.x_coords_spis = range(5, (len(self.sph_spis.dendrogram['ivl']) * 10) + 5, 10)
        self.sample_name_to_x_coord_dict_spis = {
            sample_name: x_coord for
            sample_name, x_coord in
            zip(self.sph_spis.dendrogram['ivl'], self.x_coords_spis)
        }

        self.x_coords_pver = range(5, (len(self.sph_pver.dendrogram['ivl']) * 10) + 5, 10)
        self.sample_name_to_x_coord_dict_pver = {
            sample_name: x_coord for
            sample_name, x_coord in
            zip(self.sph_pver.dendrogram['ivl'], self.x_coords_pver)
        }

        self._plot_meta_info_ax(ax=self.region_ax_spis, meta='region',  name_to_coord_dict=self.sample_name_to_x_coord_dict_spis, x_coords=self.x_coords_spis)


        self._plot_meta_info_ax(ax=self.region_ax_pver, meta='region',
                                name_to_coord_dict=self.sample_name_to_x_coord_dict_pver, x_coords=self.x_coords_pver)

        self._plot_region_leg_ax()

        self.plot_bars(sphist=self.sph_spis, bar_ax=self.seq_bars_ax_spis, seq=True)
        self.plot_bars(sphist=self.sph_pver, bar_ax=self.seq_bars_ax_pver, seq=True)

        if consolidate_profiles:
            self._consolidate_and_plot_profiles()
            foo = "bar"
        else:
            self.plot_bars(sphist=self.sph_spis, bar_ax=self.prof_bars_ax_spis, seq=False)
            self.plot_bars(sphist=self.sph_pver, bar_ax=self.prof_bars_ax_pver, seq=False)

        plt.savefig(f'dendro_bars_{dist_type}.species.split.clustered.svg')
        plt.savefig(f'dendro_bars_{dist_type}.species.split.clustered.png', dpi=1200)

    def _consolidate_and_plot_profiles(self):
        # To get the profiles color dict

        spb = SPBars(
            seq_count_table_path=self.seq_count_table_path,
            profile_count_table_path=self.profile_count_table_path,
            plot_type="profile_only", orientation='h', legend=False, relative_abundance=True,
            bar_ax=self.prof_bars_ax_spis
        )
        self.profile_color_dict = spb.profile_color_dict
        profile_count_df_abund = pd.read_csv(self.profile_count_table_path, sep='\t', skiprows=[1, 2, 3, 4, 5, 6],
                                             skipfooter=2, engine='python')
        profile_count_df_meta = pd.read_csv(self.profile_count_table_path, sep='\t', index_col=0)
        self.profile_count_df_meta = profile_count_df_meta.drop(profile_count_df_meta.columns[0], axis=1)
        profile_uid_to_profile_name_dict = {
            p_uid: p_name for p_uid, p_name in profile_count_df_meta.loc['ITS2 type profile'].items()
        }
        profile_name_to_profile_uid_dict = {
            p_name: p_uid for p_uid, p_name in profile_count_df_meta.loc['ITS2 type profile'].items()
        }

        sample_uid_to_sample_name_dict = {
            uid: p_name for uid, p_name in
            zip(profile_count_df_abund[profile_count_df_abund.columns[0]].values,
                profile_count_df_abund[profile_count_df_abund.columns[1]].values)
        }
        self.sample_name_to_sample_uid_dict = {
            p_name: uid for uid, p_name in
            zip(profile_count_df_abund[profile_count_df_abund.columns[0]].values,
                profile_count_df_abund[profile_count_df_abund.columns[1]].values)
        }

        profile_count_df_abund.set_index(keys='ITS2 type profile UID', drop=True, inplace=True)
        self.profile_count_df_abund = profile_count_df_abund.drop(profile_count_df_abund.columns[0], axis=1)
        # A dataframe that we will later modify to reflect the profile clustering
        self.profile_count_df_abund_clustered = self.profile_count_df_abund.copy()
        self.profile_count_df_abund_rel = self.profile_count_df_abund.div(self.profile_count_df_abund.sum(axis=1), axis=0)

        # Now for species for each sample, grab a list of the profiles and link this to a set of the divs
        # This dict is a profile, uid to a representative profile uid. Purely used for coloring in the plotting
        self.prof_to_rep_dict = self.cluster_profiles()
        # pickle out both of the prof_to_rep_dict s
        pickle.dump( self.prof_to_rep_dict, open( "prof_to_rep_dict.p", "wb" ) )
        # Now plot up the profiles on the plot
        self._plot_profiles(
            ax=self.prof_bars_ax_pver, host_names=self.symbiodinium_host_names_pver,
            name_to_coord_dict=self.sample_name_to_x_coord_dict_pver, repdict=self.prof_to_rep_dict,
            x_coords=self.x_coords_pver)

        # At this point we will also write out the self.profile_count_df_abund_clustered for use by the bars
        # we will do some manual modification to it to make it the write form.
        self.profile_count_df_abund_clustered.to_csv("profile_count_df_abund_clustered.csv")
        # Now plot up the profiles on the plot
        self._plot_profiles(
            ax=self.prof_bars_ax_spis, host_names=self.symbiodinium_host_names_spis,
            name_to_coord_dict=self.sample_name_to_x_coord_dict_spis, repdict=self.prof_to_rep_dict,
            x_coords=self.x_coords_spis)

        foo = "bar"

    def _plot_profiles(self, ax, host_names, name_to_coord_dict, repdict, x_coords):
        rectangles = []
        width = 10
        for sample_uid, x_coord in name_to_coord_dict.items():
            bottom = 0
            for profile_uid in self.profile_count_df_abund_rel:
                rel_abund = self.profile_count_df_abund_rel.at[sample_uid, profile_uid]
                if rel_abund != 0:
                    try:
                        color = self.profile_color_dict[repdict[profile_uid]]
                    except KeyError:
                        color = self.profile_color_dict[profile_uid]
                    rectangles.append(Rectangle(
                        (x_coord - 5, bottom),
                        width, rel_abund, ec=None, fc=color))
                    bottom += rel_abund

        patches_collection = PatchCollection(rectangles, match_original=True)
        ax.add_collection(patches_collection)
        ax.set_xlim((x_coords[0] - 5, x_coords[-1] + 5))
        ax.set_ylim(0,1)
        # Remove the axis ticks
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylabel("profiles", rotation='vertical', fontsize='xx-small')

    def cluster_profiles(self):
        profile_to_div_set_dict = defaultdict(set)
        for sample_uid in self.profile_count_df_abund.index:
            # get the list of profiles in the sample
            ser = self.profile_count_df_abund.loc[sample_uid]
            non_z = ser[ser != 0].keys()
            for prof_uid in non_z:
                if prof_uid not in profile_to_div_set_dict:
                    prof_name = self.profile_count_df_meta.at["ITS2 type profile", prof_uid]
                    prof_divs = set(filter(None, re.split("[/\-]+", prof_name)))
                    profile_to_div_set_dict[prof_uid] = prof_divs
        # Here we have a collection of all of the profiles found in the pver
        # Now work out the representatives
        rep_divs_to_profiles = defaultdict(list)
        for profile_outer, div_outer in profile_to_div_set_dict.items():
            set_of_representatives = set()
            for profile_inner, div_inner in profile_to_div_set_dict.items():
                if not profile_inner == profile_outer:
                    divs_in_common = div_outer.intersection(div_inner)
                    if len(div_outer.intersection(div_inner)) >= 3:
                        # THen these can be merged
                        divs_in_common_as_string = ",".join(sorted(divs_in_common))
                        set_of_representatives.add(divs_in_common_as_string)
            if set_of_representatives:
                if len(set_of_representatives) == 1:
                    rep_divs_to_profiles[list(set_of_representatives)[0]].append(profile_outer)
                else:
                    # Make a bunch of 3 tuples of the sets and see which of these is found
                    # in the largest number of the list_of_representatives
                    all_divs = set()
                    for div_set in set_of_representatives:
                        all_divs.update(set(div_set.split(',')))
                    three_tup_abund_dict = defaultdict(int)
                    for three_tup in itertools.combinations(all_divs, 3):
                        three_set = set(three_tup)
                        for div_str in set_of_representatives:
                            div_set = set(div_str.split(","))
                            if three_set.issubset(div_set):
                                three_tup_abund_dict[three_tup] += 1
                    # Now take the most abundant
                    sorted_tups = sorted(three_tup_abund_dict.items(), key=lambda x: x[1], reverse=True)
                    biggest = sorted_tups[0][1]
                    next = sorted_tups[1][1]
                    if biggest > next:
                        # all good
                        div_rep = ",".join(sorted(sorted_tups[0][0]))
                        rep_divs_to_profiles[div_rep].append(profile_outer)
                    else:
                        if {"C21", "C21n", "C21r"}.issubset(div_outer):
                            rep_divs_to_profiles['C21,C21n,C21r'].append(profile_outer)
                        else:
                            print("we have a problem")
        prof_to_rep_dict = {}
        # Create a new column in the profile count table
        for k, v in rep_divs_to_profiles.items():
            self.profile_count_df_abund_clustered[k] = self.profile_count_df_abund_clustered[v].sum(axis=1)
            self.profile_count_df_abund_clustered.drop(columns=list(v), inplace=True)
        for k, v in rep_divs_to_profiles.items():
            for prof_uid in v:
                prof_to_rep_dict[prof_uid] = v[0]
        return prof_to_rep_dict

    def _plot_region_leg_ax(self):
        self.region_ax_legend.set_xlim(0, 1)
        self.region_ax_legend.set_ylim(0, 1)
        r = []
        for i, region in enumerate(reversed(self.regions)):
            r.append(Rectangle((i * 0.16, 0), 0.08, 1, color=self.region_color_dict[region]))
            self.region_ax_legend.text(x=i * 0.16 + 0.09, y=0.5, s=region, va='center', fontsize='xx-small')
        patches_collection = PatchCollection(r, match_original=True)
        self.region_ax_legend.add_collection(patches_collection)
        self.region_ax_legend.set_xticks([])
        self.region_ax_legend.set_yticks([])
        self.region_ax_legend.spines['right'].set_visible(False)
        self.region_ax_legend.spines['left'].set_visible(False)
        self.region_ax_legend.spines['top'].set_visible(False)
        self.region_ax_legend.spines['bottom'].set_visible(False)
        self.region_ax_legend.text(x=0, y=-0.5, s="southernmost", va='center', fontsize='xx-small')
        self.region_ax_legend.text(x=0.8, y=-0.5, s="northernmost", va='center', fontsize='xx-small')

    def plot_bars(self, sphist, bar_ax, seq):
        # We want to plot the bars in the order of the hierarchical
        # we will use the sph.dendrogram['ivl'] uids converted to names
        dendrogram_sample_name_order = [self.symbiodinium_sample_uid_to_sample_name_dict[_] for _ in sphist.dendrogram['ivl']]
        # Now plot the bars
        if seq:
            plot_type = "seq_only"
        else:
            plot_type = "profile_only"
        spb = SPBars(
            seq_count_table_path=self.seq_count_table_path,
            profile_count_table_path=self.profile_count_table_path,
            plot_type=plot_type, orientation='h', legend=False, relative_abundance=True,
            sample_names_included=dendrogram_sample_name_order, bar_ax=bar_ax
        )
        spb.plot()
        bar_ax.set_xticks([])
        bar_ax.set_yticks([])
        if seq:
            bar_ax.set_ylabel('sequences', rotation='vertical', fontsize='xx-small')
        else:
            bar_ax.set_ylabel('profiles', rotation='vertical', fontsize='xx-small')

    def _plot_meta_info_ax(self, ax, meta, name_to_coord_dict, x_coords):
        """
        Plot up a set of meta info as categorical colors.
        :param ax: The axis on which to plot the meta info
        :param meta: Either 'region' or 'species'. The meta info being plotted
        :return: None
        """
        width = 10
        rectangles = []
        for sample_uid, x_coord in name_to_coord_dict.items():
            if self.symbiodinium_sample_uid_to_sample_name_dict[sample_uid][0] in ['S', 'P']:
                if meta == 'region':
                    c = self.region_color_dict[self.all_samples_df.at[self.symbiodinium_sample_uid_to_sample_name_dict[sample_uid], 'region']]
                    rectangles.append(Rectangle(
                        (x_coord - width / 2, 0),
                        width,
                        1, color=c))
                elif meta == 'species':
                    rectangles.append(Rectangle(
                        (x_coord - width / 2, 0),
                        width,
                        1, color=self.species_color_dict[self.symbiodinium_sample_uid_to_sample_name_dict[sample_uid][0]]))
            else:
                # negative sample
                rectangles.append(Rectangle(
                    (x_coord - width / 2, 0),
                    width,
                    1, color='black'))
        patches_collection = PatchCollection(rectangles, match_original=True)
        ax.add_collection(patches_collection)
        ax.set_xlim((x_coords[0] - width, x_coords[-1] + width))
        # Remove the axis ticks
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylabel(meta, rotation='vertical', fontsize='xx-small')

class BuitragoHier(Buitrago):
    """
    Plot up a series of dendrograms
    """
    def __init__(self, dist_type='bc'):
        super().__init__(dist_type=dist_type)

        # setup fig
        # 6 rows for the dendro and 1 for the coloring by species
        gs = gridspec.GridSpec(nrows=17, ncols=1)

        self.fig = plt.figure(figsize=(self._mm2inch(183, 80)))
        self.dendro_ax = plt.subplot(gs[:8, :])
        self.seq_bars_ax = plt.subplot(gs[8:12, :])
        self.species_ax = plt.subplot(gs[12:14, :])
        self.region_ax = plt.subplot(gs[14:16, :])
        self.region_ax_legend = plt.subplot(gs[16:17, :])

        self.sph = SPHierarchical(
            dist_output_path=self.symbiodinium_dist_path, ax=self.dendro_ax,
            sample_names_included=self.symbiodinium_host_names)
        self.sph.plot()
        self.dendro_ax.collections[0].set_linewidth(0.5)

        # We will hardcode the x coordinates as they seem to be standard for the dendrogram plots
        self.x_coords = range(5, (len(self.sph.dendrogram['ivl']) * 10) + 5, 10)
        self.sample_name_to_x_coord_dict = {
            sample_name: x_coord for
            sample_name, x_coord in
            zip(self.sph.dendrogram['ivl'], self.x_coords)
        }

        self._plot_meta_info_ax(ax=self.species_ax, meta='species')
        self._plot_meta_info_ax(ax=self.region_ax, meta='region')

        self._plot_region_leg_ax()

        self.plot_bars()

        plt.savefig(f'dendro_bars_{dist_type}.svg')
        plt.savefig(f'dendro_bars_{dist_type}.png', dpi=1200)

    def _plot_region_leg_ax(self):
        self.region_ax_legend.set_xlim(0, 1)
        self.region_ax_legend.set_ylim(0, 1)
        r = []
        for i, region in enumerate(self.regions):
            r.append(Rectangle((i * 0.16, 0), 0.08, 1, color=self.region_color_dict[region]))
            self.region_ax_legend.text(x=i * 0.16 + 0.09, y=0.5, s=region, va='center', fontsize='xx-small')
        patches_collection = PatchCollection(r, match_original=True)
        self.region_ax_legend.add_collection(patches_collection)
        self.region_ax_legend.set_xticks([])
        self.region_ax_legend.set_yticks([])

    def plot_bars(self):
        # We want to plot the bars in the order of the hierarchical
        # we will use the sph.dendrogram['ivl'] uids converted to names
        dendrogram_sample_name_order = [self.symbiodinium_sample_uid_to_sample_name_dict[_] for _ in self.sph.dendrogram['ivl']]
        # Now plot the bars
        spb = SPBars(
            seq_count_table_path=self.seq_count_table_path,
            profile_count_table_path=self.profile_count_table_path,
            plot_type='seq_only', orientation='h', legend=False, relative_abundance=True,
            sample_names_included=dendrogram_sample_name_order, bar_ax=self.seq_bars_ax, limit_genera=['A']
        )
        spb.plot()
        self.seq_bars_ax.set_xticks([])
        self.seq_bars_ax.set_yticks([])
        self.seq_bars_ax.set_ylabel('sequences', rotation='vertical', fontsize='xx-small')

    def _plot_meta_info_ax(self, ax, meta):
        """
        Plot up a set of meta info as categorical colors.
        :param ax: The axis on which to plot the meta info
        :param meta: Either 'region' or 'species'. The meta info being plotted
        :return: None
        """
        width = 10
        rectangles = []
        for sample_uid, x_coord in self.sample_name_to_x_coord_dict.items():
            if self.symbiodinium_sample_uid_to_sample_name_dict[sample_uid][0] in ['S', 'P']:
                if meta == 'region':
                    c = self.region_color_dict[self.all_samples_df.at[self.symbiodinium_sample_uid_to_sample_name_dict[sample_uid], 'region']]
                    rectangles.append(Rectangle(
                        (x_coord - width / 2, 0),
                        width,
                        1, color=c))
                elif meta == 'species':
                    rectangles.append(Rectangle(
                        (x_coord - width / 2, 0),
                        width,
                        1, color=self.species_color_dict[self.symbiodinium_sample_uid_to_sample_name_dict[sample_uid][0]]))
            else:
                # negative sample
                rectangles.append(Rectangle(
                    (x_coord - width / 2, 0),
                    width,
                    1, color='black'))
        patches_collection = PatchCollection(rectangles, match_original=True)
        ax.add_collection(patches_collection)
        ax.set_xlim((self.x_coords[0] - width, self.x_coords[-1] + width))
        # Remove the axis ticks
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylabel(meta, rotation='vertical', fontsize='xx-small')

class BuitragoBars(Buitrago):
    def __init__(self, dist_type='bc', cluster_profiles=True):
        super().__init__(dist_type)
        self.bar_figures_dir = os.path.join(self.root_dir, "bar_figures")
        # self.fig = plt.figure(figsize=self._mm2inch((200, 320)))
        # bars to legends at ratio of 4:1
        gs = gridspec.GridSpec(nrows=4, ncols=6)
        # Then we need to look at ordinations and hierarchical clustering and annotating accorrding to the site
        # and reef.
        # There will be 6 axes for plotting and 3 legend axes
        # 2 sets of 3 one for each
        if cluster_profiles:
            self.titles = ['pver_genera', 'pver_seq', 'pver_profile_clustered', 'spis_genera', 'spis_seq', 'spis_profile_clustered']
        else:
            self.titles = ['pver_genera', 'pver_seq', 'pver_profile', 'spis_genera', 'spis_seq', 'spis_profile']


        # create an instance of SPBars just to generate a seq and profile dict for the whole dataset
        # then use this dictionary for plotting the actual plots.
        if cluster_profiles:
            self.profile_count_table_path = "/Users/benjaminhume/Documents/projects/20210113_buitrago/ITS2/131_20201203_DBV_20201207T095144.profiles.absolute.abund_and_meta.clustered.txt"

        # We want to work out the number of profiles before and after clustering in spis and pver samples
        # This code works. Just uncomment to do the plotting.
        prof_count_df = pd.read_table(self.profile_count_table_path)
        prof_count_df = prof_count_df.iloc[6:,]
        cols = list(prof_count_df)
        cols[1] = "sample_name"
        prof_count_df.columns = cols
        prof_count_df = prof_count_df.set_index("sample_name")
        prof_count_df = prof_count_df.iloc[:-2,1:].astype(float).astype(int)
        pver_profiles = set()
        pver_maj_profiles = defaultdict(int)
        for sample in self.pver_df.index:
            ser = prof_count_df.loc[sample]
            pver_maj_profiles[ser.idxmax()] += 1
            non_zero_profiles = list(ser[ser!=0].index)
            pver_profiles.update(non_zero_profiles)
        pver_maj_tot = sum(pver_maj_profiles.values())
        tot = 0
        pver_cum = [0]
        for k, v in sorted(pver_maj_profiles.items(), key=lambda x:x[1], reverse=True):
            tot += v
            print(f"{k}:{tot/pver_maj_tot}")
            pver_cum.append(tot/pver_maj_tot)
        print("\n\n\n")

        spis_profiles = set()
        spis_maj_profiles = defaultdict(int)
        for sample in self.spis_df.index:
            ser = prof_count_df.loc[sample]
            spis_maj_profiles[ser.idxmax()] += 1
            non_zero_profiles = list(ser[ser != 0].index)
            spis_profiles.update(non_zero_profiles)

        spis_maj_tot = sum(spis_maj_profiles.values())
        tot = 0
        spis_cum = [0]
        for k, v in sorted(spis_maj_profiles.items(), key=lambda x: x[1], reverse=True):
            tot += v
            print(f"{k}:{tot/spis_maj_tot}")
            spis_cum.append(tot/spis_maj_tot)
        print("\n\n\n")
        print(f"When clustering is {cluster_profiles}; pver has {len(pver_profiles)} profiles, spis has {len(spis_profiles)}.")
        print(f"\tOr when considering only most abundant profiles; pver has {len(pver_maj_profiles)} profiles, spis has {len(spis_maj_profiles)}.")

        # simpsons index = 0.054
        skbio.diversity.alpha_diversity(metric="dominance", counts=list(spis_maj_profiles.values()))
        # simpsons index = 0.477
        skbio.diversity.alpha_diversity(metric="dominance", counts=list(pver_maj_profiles.values()))

        pver_numbers = [_[1]/pver_maj_tot for _ in sorted(pver_maj_profiles.items(), key=lambda x: x[1], reverse=True)]
        spis_numbers = [_[1]/spis_maj_tot for _ in sorted(spis_maj_profiles.items(), key=lambda x: x[1], reverse=True)]
        fig, ax = plt.subplots(nrows=1, ncols=1)
        ax.plot(range(len(spis_cum)), spis_cum, 'b--', label='spis')
        ax.plot(range(len(pver_cum)), pver_cum, 'r--', label='pver')
        ax.legend()
        ax.set_ylabel("Cumulative proportion of samples represented")
        ax.set_xlabel("Number of ITS2 profiles")
        plt.savefig(f"ITS2.profile.cumul.prop.clustering.{cluster_profiles}.svg")
        plt.savefig(f"ITS2.profile.cumul.prop.clustering.{cluster_profiles}.png", dpi=600)
        foo = 'bar'

        spb = SPBars(
            seq_count_table_path=self.seq_count_table_path,
            profile_count_table_path=self.profile_count_table_path,
            plot_type='seq_and_profile', orientation='v', legend=False, relative_abundance=True, no_plotting=True
        )
        self.seq_color_dict = spb.seq_color_dict
        self.profile_color_dict = spb.profile_color_dict

        config_tups = [
            ('seq_only', self.seq_color_dict, None, True),
            ('seq_only', self.seq_color_dict, None, False),
            ('profile_only', None, self.profile_color_dict, False)]
        # Now we can plot up each of the axes

        for i, df in enumerate([self.pver_df, self.spis_df]):
            for j, (plot_type, seq_color_dict, profile_color_dict, color_by_genus) in enumerate(config_tups):
                fig, ax = plt.subplots(ncols=1, nrows=2, figsize=self._mm2inch((320, 200)))
                if plot_type == "seq_only":
                    if color_by_genus:
                        sp_bars = SPBars(
                            seq_count_table_path=self.seq_count_table_path,
                            profile_count_table_path=self.profile_count_table_path,
                            plot_type=plot_type, orientation='h', legend=True, relative_abundance=True,
                            color_by_genus=color_by_genus, sample_outline=False,
                            sample_names_included=df.index.values,
                            bar_ax=ax[0], genera_leg_ax=ax[1], seq_color_dict=seq_color_dict,
                            profile_color_dict=profile_color_dict
                        )
                    else:
                        sp_bars = SPBars(
                            seq_count_table_path=self.seq_count_table_path,
                            profile_count_table_path=self.profile_count_table_path,
                            plot_type=plot_type, orientation='h', legend=True, relative_abundance=True,
                            color_by_genus=color_by_genus, sample_outline=False, sample_names_included=df.index.values,
                            bar_ax=ax[0], seq_leg_ax=ax[1], seq_color_dict=seq_color_dict,
                            profile_color_dict=profile_color_dict
                        )
                    sp_bars.plot()
                if plot_type == "profile_only":
                    sp_bars = SPBars(
                        seq_count_table_path=self.seq_count_table_path,
                        profile_count_table_path=self.profile_count_table_path,
                        plot_type=plot_type, orientation='h', legend=True, relative_abundance=True,
                        color_by_genus=color_by_genus, sample_outline=False, sample_names_included=df.index.values,
                        bar_ax=ax[0], profile_leg_ax=ax[1], seq_color_dict=seq_color_dict,
                        profile_color_dict=profile_color_dict
                    )
                    sp_bars.plot()
                # Now annotate and save the figure
                ax[0].set_xticks([])
                ax[0].set_yticks([])
                ax[0].set_title(self.titles[(3*i)+j], fontsize='small')
                # Need to add a black line for each of the reef borders
                reef = df.iloc[0]["reef"]
                lines = []
                line_colors = []
                line_widths = []
                for k, ind in enumerate(df.index.values):
                    new_reef = df.at[ind, "reef"]
                    if new_reef != reef:
                        reef = new_reef
                        # Then we need to plot a black line at k - 0.5
                        lines.append(k-0.5)
                        line_colors.append("black")
                        line_widths.append(2)
                ax[0].vlines(x=lines, ymin=0, ymax=1, colors=line_colors, linewidths=line_widths)
                plt.savefig(os.path.join(self.plotting_dir, f"{self.titles[(3 * i) + j]}.bars.svg"))
                plt.savefig(os.path.join(self.plotting_dir, f"{self.titles[(3*i)+j]}.bars.pdf"))
                plt.savefig(os.path.join(self.plotting_dir, f"{self.titles[(3*i)+j]}.bars.png",), dpi=600)
                plt.close(fig)
                foo = "bar"

class BuitragoBars_clustered_profiles(Buitrago):
    def __init__(self, dist_type='bc', cluster_profiles=True):
        super().__init__(dist_type)
        self.bar_figures_dir = os.path.join(self.root_dir, "bar_figures")
        # self.fig = plt.figure(figsize=self._mm2inch((200, 320)))
        # bars to legends at ratio of 4:1
        gs = gridspec.GridSpec(nrows=4, ncols=6)
        # Then we need to look at ordinations and hierarchical clustering and annotating according to the site
        # and reef.
        # There will be 6 axes for plotting and 3 legend axes
        # 2 sets of 3 one for each
        if cluster_profiles:
            self.titles = ['pver_genera', 'pver_seq', 'pver_profile_clustered', 'spis_genera', 'spis_seq', 'spis_profile_clustered']
        else:
            self.titles = ['pver_genera', 'pver_seq', 'pver_profile', 'spis_genera', 'spis_seq', 'spis_profile']


        # Use the clustered profiles
        # This file was created manually using Excel.
        self.profile_count_table_path = "/Users/benjaminhume/Documents/projects/20210113_buitrago/ITS2/131_20201203_DBV_20201207T095144.profiles.absolute.abund_and_meta.clustered.tsv"

        # We want to work out the number of profiles before and after clustering in spis and pver samples
        # This code works. Just uncomment to do the plotting.
        prof_count_df = pd.read_table(self.profile_count_table_path)
        prof_count_df = prof_count_df.iloc[6:,]
        cols = list(prof_count_df)
        cols[1] = "sample_name"
        prof_count_df.columns = cols
        prof_count_df = prof_count_df.set_index("sample_name")
        prof_count_df = prof_count_df.iloc[:-2,1:].astype(float).astype(int)
        pver_profiles = set()
        pver_maj_profiles = defaultdict(int)

        # Work out the number of samples with one profile
        pver_prof_df = prof_count_df.loc[self.pver_df.index, :]
        pver_one_profile_sample = []
        for ind, ser in pver_prof_df.iterrows():
            ser_non_zero = ser[ser!=0]
            if len(ser_non_zero) == 1:
                pver_one_profile_sample.append(ind)
        
        # Proportion of samples
        pver_one_prof_prop = len(pver_one_profile_sample) / len(pver_prof_df.index)
        print(f"The proportion of samples with a single profile in pver is {pver_one_prof_prop}")

        spis_prof_df = prof_count_df.loc[self.spis_df.index, :]
        spis_one_profile_sample = []
        for ind, ser in spis_prof_df.iterrows():
            ser_non_zero = ser[ser != 0]
            if len(ser_non_zero) == 1:
                spis_one_profile_sample.append(ind)
        
        # Proportion of samples
        spis_one_prof_prop = len(spis_one_profile_sample) / len(spis_prof_df.index)
        print(f"The proportion of samples with a single profile in spis is {spis_one_prof_prop}")

        # Then work this out for only those samples from MAQ
        pver_prof_df_MAQ = prof_count_df.loc[[_ for _ in self.pver_df.index if "MAQ" in _], :]
        pver__more_than_one_profile_sample = []
        for ind, ser in pver_prof_df_MAQ.iterrows():
            ser_non_zero = ser[ser != 0]
            if len(ser_non_zero) > 1:
                pver__more_than_one_profile_sample.append(ind)
        
        # Proportion of samples
        pver_more_than_one_prof_prop = len(pver__more_than_one_profile_sample) / len([_ for _ in self.pver_df.index if "MAQ" in _])
        print(f"The proportion of samples with more than a single profile in pver is {pver_more_than_one_prof_prop}")

        spis_prof_df_MAQ = prof_count_df.loc[[_ for _ in self.spis_df.index if "MAQ" in _], :]
        spis__more_than_one_profile_sample = []
        for ind, ser in spis_prof_df_MAQ.iterrows():
            ser_non_zero = ser[ser != 0]
            if len(ser_non_zero) == 1:
                spis__more_than_one_profile_sample.append(ind)
        
        # Proportion of samples
        spis_more_than_one_prof_prop = len(spis__more_than_one_profile_sample) / len([_ for _ in self.spis_df.index if "MAQ" in _])
        print(f"The proportion of samples with a single profile in spis is {spis_more_than_one_prof_prop}")

        foo = "bar"

        for sample in self.pver_df.index:
            ser = prof_count_df.loc[sample]
            pver_maj_profiles[ser.idxmax()] += 1
            non_zero_profiles = list(ser[ser!=0].index)
            pver_profiles.update(non_zero_profiles)
        pver_maj_tot = sum(pver_maj_profiles.values())
        tot = 0
        pver_cum = [0]
        for k, v in sorted(pver_maj_profiles.items(), key=lambda x:x[1], reverse=True):
            tot += v
            print(f"{k}:{tot/pver_maj_tot}")
            pver_cum.append(tot/pver_maj_tot)
        print("\n\n\n")

        spis_profiles = set()
        spis_maj_profiles = defaultdict(int)
        for sample in self.spis_df.index:
            ser = prof_count_df.loc[sample]
            spis_maj_profiles[ser.idxmax()] += 1
            non_zero_profiles = list(ser[ser != 0].index)
            spis_profiles.update(non_zero_profiles)

        spis_maj_tot = sum(spis_maj_profiles.values())
        tot = 0
        spis_cum = [0]
        for k, v in sorted(spis_maj_profiles.items(), key=lambda x: x[1], reverse=True):
            tot += v
            print(f"{k}:{tot/spis_maj_tot}")
            spis_cum.append(tot/spis_maj_tot)
        print("\n\n\n")
        print(f"When clustering is {cluster_profiles}; pver has {len(pver_profiles)} profiles, spis has {len(spis_profiles)}.")
        print(f"\tOr when considering only most abundant profiles; pver has {len(pver_maj_profiles)} profiles, spis has {len(spis_maj_profiles)}.")

        # simpsons index = 0.054
        skbio.diversity.alpha_diversity(metric="dominance", counts=list(spis_maj_profiles.values()))
        # simpsons index = 0.477
        skbio.diversity.alpha_diversity(metric="dominance", counts=list(pver_maj_profiles.values()))

        pver_numbers = [_[1]/pver_maj_tot for _ in sorted(pver_maj_profiles.items(), key=lambda x: x[1], reverse=True)]
        spis_numbers = [_[1]/spis_maj_tot for _ in sorted(spis_maj_profiles.items(), key=lambda x: x[1], reverse=True)]
        fig, ax = plt.subplots(nrows=1, ncols=1)
        ax.plot(range(len(spis_cum)), spis_cum, 'b--', label='spis')
        ax.plot(range(len(pver_cum)), pver_cum, 'r--', label='pver')
        ax.legend()
        ax.set_ylabel("Cumulative proportion of samples represented")
        ax.set_xlabel("Number of ITS2 profiles")
        plt.savefig(f"ITS2.profile.cumul.prop.clustering.{cluster_profiles}.svg")
        plt.savefig(f"ITS2.profile.cumul.prop.clustering.{cluster_profiles}.png", dpi=600)
        foo = 'bar'

        spb = SPBars(
            seq_count_table_path=self.seq_count_table_path,
            profile_count_table_path=self.profile_count_table_path,
            plot_type='seq_and_profile', orientation='v', legend=False, relative_abundance=True, no_plotting=True, num_profile_leg_cols=67
        )

        # we want to know what proportion of the profiles for each species were Symbiodinium and Cladocopium
        pver_prof_num_dict = defaultdict(int)
        for ind, ser in pver_prof_df.iterrows():
            prof_uids = list(ser[ser!=0].index)
            prof_names = [spb.profile_uid_to_profile_name_dict[prof_uid] for prof_uid in prof_uids]
            for prof_name in prof_names:
                if prof_name.startswith("A"):
                    pver_prof_num_dict["A"] += 1
                elif prof_name.startswith("C"):
                    pver_prof_num_dict["C"] += 1
                else:
                    pver_prof_num_dict["other"] += 1
        a_prop = pver_prof_num_dict["A"]/ sum(pver_prof_num_dict.values())
        c_prop = pver_prof_num_dict["C"] / sum(pver_prof_num_dict.values())
        print(f"{a_prop} of the detected profiles instances in pver were Symbiodinium")
        print(f"{c_prop} of the detected profiles instances in pver were Cladocopium")

        spis_prof_num_dict = defaultdict(int)
        for ind, ser in spis_prof_df.iterrows():
            prof_uids = list(ser[ser != 0].index)
            prof_names = [spb.profile_uid_to_profile_name_dict[prof_uid] for prof_uid in prof_uids]
            for prof_name in prof_names:
                if prof_name.startswith("A"):
                    spis_prof_num_dict["A"] += 1
                elif prof_name.startswith("C"):
                    spis_prof_num_dict["C"] += 1
                else:
                    spis_prof_num_dict["other"] += 1
        spisa_prop = spis_prof_num_dict["A"] / sum(spis_prof_num_dict.values())
        spisc_prop = spis_prof_num_dict["C"] / sum(spis_prof_num_dict.values())
        print(f"{spisa_prop} of the detected profiles instances in spis were Symbiodinium")
        print(f"{spisc_prop} of the detected profiles instances in spis were Cladocopium")

        foo = "bar"
        self.seq_color_dict = spb.seq_color_dict
        self.profile_color_dict = spb.profile_color_dict
        fig, ax_arr = plt.subplots(ncols=4, nrows=1, figsize=self._mm2inch((400, 320)))
        if os.path.exists("profile_color_dict.no_gen.p"):
            self.profile_color_dict = pickle.load(open("profile_color_dict.no_gen.p", "rb"))
        
        # # Now we can plot up each of the axes
        # # Reverse the dfs so that we are plotting top to bottom
        pver_rev_df = self.pver_df.iloc[::-1]
        spis_rev_df = self.spis_df.iloc[::-1]
        for i, (df, species, ax) in enumerate(zip([pver_rev_df, spis_rev_df], ["pver", "spis"], [(ax_arr[0], ax_arr[1]), (ax_arr[2], ax_arr[3])])):

            sp_bars = SPBars(
                seq_count_table_path=self.seq_count_table_path,
                profile_count_table_path=self.profile_count_table_path,
                plot_type="profile_only", orientation='v', legend=True, relative_abundance=True,
                sample_outline=False, sample_names_included=df.index.values,
                bar_ax=ax[0], profile_leg_ax=ax[1],
                profile_color_dict=self.profile_color_dict, num_profile_leg_cols=67
            )
            sp_bars.plot()

            # Now annotate and save the figure
            ax[0].set_xticks([])
            ax[0].set_yticks([])
            ax[0].set_title(f"clustered_profiles_{species}", fontsize='small')
            # Need to add a black line for each of the reef borders
            reef = df.iloc[0]["reef"]
            lines = []
            line_colors = []
            line_widths = []
            for k, ind in enumerate(df.index.values):
                new_reef = df.at[ind, "reef"]
                if new_reef != reef:
                    reef = new_reef
                    # Then we need to plot a black line at k - 0.5
                    lines.append(k - 0.5)
                    line_colors.append("black")
                    line_widths.append(2)
            ax[0].hlines(y=lines, xmin=0, xmax=1, colors=line_colors, linewidths=line_widths)
        plt.savefig(os.path.join(self.plotting_dir, f"clustered_profiles.bars.svg"))
        plt.savefig(os.path.join(self.plotting_dir, f"clustered_profiles.bars.pdf"))
        plt.savefig(os.path.join(self.plotting_dir, f"clustered_profiles.bars.png", ), dpi=600)
        plt.close(fig)
        
        # output a good profile colour dict so that we can work with it again
        if not os.path.exists("profile_color_dict.no_gen.p"):
            pickle.dump(self.profile_color_dict, open("profile_color_dict.no_gen.p", "wb"))

        plt.close()


        # Plot up the genera
        fig, ax_arr = plt.subplots(ncols=4, nrows=1, figsize=self._mm2inch((400, 320)))
        for i, (df, species, ax) in enumerate(zip([pver_rev_df, spis_rev_df], ["pver", "spis"], [(ax_arr[0], ax_arr[1]), (ax_arr[2], ax_arr[3])])):

            sp_bars = SPBars(
                seq_count_table_path=self.seq_count_table_path,
                profile_count_table_path=self.profile_count_table_path,
                plot_type="seq_only", orientation='v', legend=True, relative_abundance=True, color_by_genus=True,
                sample_outline=False, sample_names_included=df.index.values,
                bar_ax=ax[0], genera_leg_ax=ax[1],
                profile_color_dict=self.profile_color_dict, num_profile_leg_cols=67
            )
            sp_bars.plot()

            # Now annotate and save the figure
            ax[0].set_xticks([])
            ax[0].set_yticks([])
            ax[0].set_title(f"genera_{species}", fontsize='small')
            # Need to add a black line for each of the reef borders
            reef = df.iloc[0]["reef"]
            lines = []
            line_colors = []
            line_widths = []
            for k, ind in enumerate(df.index.values):
                new_reef = df.at[ind, "reef"]
                if new_reef != reef:
                    reef = new_reef
                    # Then we need to plot a black line at k - 0.5
                    lines.append(k - 0.5)
                    line_colors.append("black")
                    line_widths.append(2)
            ax[0].hlines(y=lines, xmin=0, xmax=1, colors=line_colors, linewidths=line_widths)
        plt.savefig(os.path.join(self.plotting_dir, f"clustered_profiles_genera.bars.svg"))
        plt.savefig(os.path.join(self.plotting_dir, f"clustered_profiles_genera.bars.pdf"))
        plt.savefig(os.path.join(self.plotting_dir, f"clustered_profiles_genera.bars.png", ), dpi=600)
        plt.close(fig)
        foo = "bar"

class CalculateAverageProfDistances(Buitrago):
    """ A class dedicated to calculating the average profile nearest neighbour distance"""
    def __init__(self):
        super().__init__("bc")
        dist_path_A = "/Users/benjaminhume/Documents/projects/20210113_buitrago/ITS2/sp_output/between_profile_distances/A/20201207T095144_braycurtis_profile_distances_A_sqrt.dist"
        dist_path_C = "/Users/benjaminhume/Documents/projects/20210113_buitrago/ITS2/sp_output/between_profile_distances/C/20201207T095144_braycurtis_profile_distances_C_sqrt.dist"
        dist_path_D = "/Users/benjaminhume/Documents/projects/20210113_buitrago/ITS2/sp_output/between_profile_distances/D/20201207T095144_braycurtis_profile_distances_D_sqrt.dist"

        profile_count_table_path = "/Users/benjaminhume/Documents/projects/20210113_buitrago/ITS2/sp_output/its2_type_profiles/131_20201203_DBV_20201207T095144.profiles.absolute.abund_and_meta.txt"

        # We want to work out the number of profiles before and after clustering in spis and pver samples
        prof_count_df = pd.read_table(profile_count_table_path)
        profile_uid_to_profile_name_dict = {int(uid): name for uid, name in zip(list(prof_count_df)[2:], list(prof_count_df.iloc[5,2:].values))}
        prof_count_df = prof_count_df.iloc[6:, ]
        cols = list(prof_count_df)
        cols[1] = "sample_name"
        prof_count_df.columns = cols
        prof_count_df = prof_count_df.set_index("sample_name")
        prof_count_df = prof_count_df.iloc[:-2, 1:].astype(float).astype(int)
        prof_count_df.columns = [int(_) for _ in list(prof_count_df)]

        sym_dist_df_A = pd.read_table(dist_path_A, header=None)
        sym_dist_df_A.index = sym_dist_df_A[1]
        sym_dist_df_A = sym_dist_df_A.iloc[:,2:]
        sym_dist_df_A.columns = sym_dist_df_A.index.values

        sym_dist_df_C = pd.read_table(dist_path_C, header=None)
        sym_dist_df_C.index = sym_dist_df_C[1]
        sym_dist_df_C = sym_dist_df_C.iloc[:, 2:]
        sym_dist_df_C.columns = sym_dist_df_C.index.values

        sym_dist_df_D = pd.read_table(dist_path_D, header=None)
        sym_dist_df_D.index = sym_dist_df_D[1]
        sym_dist_df_D = sym_dist_df_D.iloc[:, 2:]
        sym_dist_df_D.columns = sym_dist_df_D.index.values

        # create a dictionary that holds the distance to the nearest profile for every profile
        profile_uid_to_nearest_profile_dist_dict = {}
        for prof_uid, ser in sym_dist_df_A.iterrows():
            nearest_match_uid = sorted(ser.items(), key=lambda x: x[1])[1][0]
            # Get the number of divs in common
            match_name = profile_uid_to_profile_name_dict[nearest_match_uid]
            our_name = profile_uid_to_profile_name_dict[prof_uid]
            match_divs = set(filter(None, re.split("[/\-]+", match_name)))
            ours_divs = set(filter(None, re.split("[/\-]+", our_name)))
            profile_uid_to_nearest_profile_dist_dict[prof_uid] = len(match_divs.intersection(ours_divs))


        for prof_uid, ser in sym_dist_df_C.iterrows():
            nearest_match_uid = sorted(ser.items(), key=lambda x: x[1])[1][0]
            # Get the number of divs in common
            match_name = profile_uid_to_profile_name_dict[nearest_match_uid]
            our_name = profile_uid_to_profile_name_dict[prof_uid]
            match_divs = set(filter(None, re.split("[/\-]+", match_name)))
            ours_divs = set(filter(None, re.split("[/\-]+", our_name)))
            profile_uid_to_nearest_profile_dist_dict[prof_uid] = len(match_divs.intersection(ours_divs))
        for prof_uid, ser in sym_dist_df_D.iterrows():
            nearest_match_uid = sorted(ser.items(), key=lambda x: x[1])[1][0]
            # Get the number of divs in common
            match_name = profile_uid_to_profile_name_dict[nearest_match_uid]
            our_name = profile_uid_to_profile_name_dict[prof_uid]
            match_divs = set(filter(None, re.split("[/\-]+", match_name)))
            ours_divs = set(filter(None, re.split("[/\-]+", our_name)))
            profile_uid_to_nearest_profile_dist_dict[prof_uid] = len(match_divs.intersection(ours_divs))

        pver_instance_list = []
        for sample in self.pver_df.index:
            ser = prof_count_df.loc[sample]
            # if profile_uid_to_profile_name_dict[ser.idxmax()].startswith("A"):
            #     pver_instance_list.append(ser.idxmax())
            # else:
            #     continue
            uid_list = [_ for _ in ser[ser!=0].index]
            pver_instance_list += uid_list

        pver_distances = []
        # Here instead of doing pairwise distance, we want to find the closest profile and log that distance
        for prof_uid in pver_instance_list:
            pver_distances.append(profile_uid_to_nearest_profile_dist_dict[prof_uid])
        # now the average
        pver_av_profile_instance_dist = sum(pver_distances)/len(pver_distances)

        spis_instance_list = []
        for sample in self.spis_df.index:
            ser = prof_count_df.loc[sample]
            # We can do this for all clades now
            # if profile_uid_to_profile_name_dict[ser.idxmax()].startswith("A"):
            #     pver_instance_list.append(ser.idxmax())
            # else:
            #     continue
            uid_list = [_ for _ in ser[ser!=0].index]
            spis_instance_list += uid_list

        spis_distances = []
        err_count = 0
        # Here instead of doing pairwise distance, we want to find the closest profile and log that distance
        for prof_uid in spis_instance_list:
            try:
                spis_distances.append(profile_uid_to_nearest_profile_dist_dict[prof_uid])
            except KeyError:
                err_count += 1
                continue

        # now the average
        spis_av_profile_instance_dist = sum(spis_distances) / len(spis_distances)
        foo = "bar"



# For plotting the ordinations
# BuitragoOrdinations(dist_type='bc')

# For plotting the dendrogram figure with associated meta info and sequences
# BuitragoHier(dist_type='bc')
# For plotting the dendogram split by species and with the option of clustering the profiles
# BuitragoHier_split_species(dist_type='bc')

# For plotting the north to south genera, sequence, and profile bars for each species
# BuitragoBars()

# A modification of the original BuitragoBars to do custom colours of the clustered profiles plot
BuitragoBars_clustered_profiles()

CalculateAverageProfDistances()
