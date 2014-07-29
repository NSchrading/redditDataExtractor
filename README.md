redditDataExtractor
===================

![Main application](http://i.imgur.com/ekuaFS9.png)


The reddit Data Extractor is a GUI tool for downloading almost any content posted to reddit. Downloads from specific users, specific subreddits, users by subreddit, and with filters on the content is supported. Some intelligence is built in to attempt to avoid downloading duplicate external content.

For data scientists and curious redditors, JSON-encoded text files can be extracted for analysis. These contain all the characteristics of reddit submissions, including the title, a hierarchy of comments, the score, selftext, creation date, and more. Below is a snippet of the attributes that are retrieved.

![JSON encoded submission data](http://i.imgur.com/lKxB3Hl.png)


For redditors who want to easily retrieve submitted images, gifs, and webms, or for people interested in training machine learning applications that link semantic content (submission data) with images, the reddit data extractor supports you as well. Imgur, Gfycat, Vidble, and Minus are specifically supported, and any direct link to an image should work as well.

External content can be downloaded from submission links, comments, and selftext.

Filters can be set to download only those submissions, or those submission's external content, passing the filter criteria.

Here are all the settings available:
![Settings](http://i.imgur.com/f874li1.png)

<dl>
  <dt>The following file types are supported:</dt>
  <dd>jpg, png, gif, webm</dd>
</dl>
  
<dl>
  <dt>Site specific notes:</dt>
  <dd>Imgur page, gallery, and album links will only be downloadable if you obtain an Imgur API client-id and enter it into the reddit data extractor.</dd>
  <dd>Minus galleries are not currently supported - only page and direct links.</dd>
</dl>
