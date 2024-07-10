library(ggplot2)
library(data.table)
library(magrittr)
library(dplyr)

taxon_df = as.data.frame(fread("results/cells_by_taxon.csv"))

my_theme = theme(axis.text.x = element_text(angle = 45,
 vjust = 1,
 hjust=1))

plot_by_taxa <- taxon_df %>%
  tail(5) %>%
  ggplot(aes(x = reorder(taxon_name, -taxon), y = taxon))  + 
   geom_point() +
   ylab("Cell items") +
   xlab("Taxon" ) +
   theme_bw() +
   my_theme


editors_df = as.data.frame(fread("results/cells_wikidata_editors.csv"))
editors_df <- editors_df[,c("username", "count","qid")]

total_edits <- editors_df %>%
    group_by(username) %>%
    summarise(total_edits = sum(count)) %>%
    arrange(total_edits) %>%
    tail(10) %>%
    ggplot(aes(x = reorder(username, -total_edits), y = total_edits))  + 
      geom_point() +
      ylab("Total edits on cell items") +
      xlab("Username" ) +
      theme_bw() +
      my_theme 

 total_edited_items <- editors_df %>%
    group_by(username) %>%
     mutate(edited_items = n())%>%
     arrange(edited_items) %>%
     select(c("username", "edited_items")) %>%
     distinct() %>%
    tail(10) %>%
    ggplot(aes(x = reorder(username, -edited_items), y = edited_items))  + 
      geom_point() +
      ylab("Edited items") +
      xlab("Username" ) +
      theme_bw() +
      my_theme

   
creators_df = as.data.frame(fread("results/cells_wikidata_authors.csv"))

 total_created_items <- creators_df %>%
    arrange(count) %>%
    tail(10) %>%
            ggplot(aes(x = reorder(author, -count), y = count))  + 
      geom_point() +
      ylab("Created items") +
      xlab("Username" ) +
      theme_bw() +
      my_theme


library(patchwork)
p <- (plot_by_taxa + total_created_items) / ( total_edits + total_edited_items)

p + plot_annotation(tag_levels = 'A')
ggsave("results/statistics.png", height=6, width=8)
