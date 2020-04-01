from process_blast_alignments import count_overlap
import gffutils


def get_remap_gene(gene, gene_dict):
    for feature in gene_dict[gene]:
        if feature.featuretype == "gene":
            return feature


def get_gene_index(gene, gene_list):
    for i in range(len(gene_list)):
        if gene_list[i].id == gene.id:
            return i


def check_homologues_partial(gene_list, gene_index_list, db_name, genes):
    gene_db = gffutils.FeatureDB(db_name)
    remap_genes = {}
    for gene in genes:
        overlapping_genes = gene_list[gene_index_list[gene.seqid]:]
        compare_overlapping_genes(overlapping_genes, gene_db, gene, remap_genes)
    return remap_genes


def check_homologues(lifted_features_to_check, feature_list, db_name, processes):
    gene_list = get_gene_list(feature_list)
    gene_list.sort(key = lambda x: (x.seqid, x.start))
    genes_to_check = get_gene_list(lifted_features_to_check)
    gene_db = gffutils.FeatureDB(db_name)
    gene_index_list = {}
    gene_index = 0
    for gene in gene_list:
        if gene.seqid not in gene_index_list:
            gene_index_list[gene.seqid] = gene_index
        gene_index += 1
    remap_genes = {}
    for gene in genes_to_check:
        print(gene.id)
        overlapping_genes = gene_list[gene_index_list[gene.seqid]:]
        compare_overlapping_genes(overlapping_genes, gene_db, gene, remap_genes)
    return remap_genes


def get_gene_list(feature_list):
    gene_list = []
    for feature in feature_list:
        for value in feature_list[feature]:
            if value.featuretype == "gene":
                gene_list.append(value)
    return gene_list


def compare_overlapping_genes(overlapping_genes, gene_db, gene, remap_genes):
    for overlap_gene in overlapping_genes:
        if overlap_gene.id != gene.id and gene.strand == overlap_gene.strand:
            if overlap_gene.seqid != gene.seqid or overlap_gene.start > gene.end:
                break
            if overlap_gene.end < gene.start:
                continue
            else:
                original_overlap_gene = gene_db[overlap_gene.id[:-len(overlap_gene.id.split("_")[-1])-1]]
                original_gene = gene_db[gene.id[:-len(gene.id.split("_")[-1])-1]]
                if original_overlap_gene.seqid != original_gene.seqid or original_overlap_gene.strand != original_gene.strand or original_overlap_gene.id == original_gene.id:
                    original_overlap = -1
                else:
                    original_overlap = count_overlap(original_gene.start, original_gene.end, original_overlap_gene.start,
                                                 original_overlap_gene.end)
                lifted_overlap = count_overlap(gene.start, gene.end, overlap_gene.start, overlap_gene.end)
                if lifted_overlap >0 and original_overlap <= 0:
                    gene_to_remap, gene_to_keep = find_gene_to_remap(gene, overlap_gene)
                    coords = [gene_to_remap.start, gene_to_remap.end, gene_to_keep.start, gene_to_keep.end]
                    coords.sort()
                    remap_genes[gene_to_remap.id] = [coords[1], coords[2], gene_to_remap.seqid, gene_to_remap.strand]
    return remap_genes


def find_gene_to_remap(gene, overlap_gene):
    if gene.score < overlap_gene.score:
        return overlap_gene, gene
    elif overlap_gene.score < gene.score:
        return gene, overlap_gene
    else:
        if overlap_gene.end - overlap_gene.start < gene.end - gene.start:
            return overlap_gene, gene
        elif overlap_gene.end - overlap_gene.start >  gene.end - gene.start:
            return gene, overlap_gene
        else:
            min_gene = min(gene.id, overlap_gene.id)
            if min_gene == gene.id:
                return gene, overlap_gene
            else:
                return overlap_gene, gene
