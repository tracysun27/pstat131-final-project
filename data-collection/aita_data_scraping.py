import praw
import pandas as pd
import datetime

CLIENT_ID = 'rqV5kJuXLHYoBZ-iY7C5HA'
CLIENT_SECRET = 'T4cxGlYly94kDX6DMPwslDoAxZ8bJg'

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     user_agent = "Gathering r/aita data script v1.0 by /u/mediochre_")

# checking if it works:
# print(reddit.read_only) # Output: True
 
# getting flairs:
# flairs = {}
# for submission in reddit.subreddit('AmItheAsshole').hot(limit=500):
#     # print("Title:", submission.title)
#     # print("Post:", submission.selftext)
#     # print("Upvote percentage:", submission.upvote_ratio)
#     if submission.link_flair_text != None:
#         if submission.link_flair_template_id not in flairs:
#             flairs[submission.link_flair_template_id] = submission.link_flair_text
#         # print("Flair:", submission.link_flair_text, submission.link_flair_template_id)
#         # print()
# print(flairs)

# obtained flairs:
flairs = {'47fdebc0-d3af-11e8-80cb-0e369ce83cd4': 'META', 
          'e78edef2-b1ef-11ec-9f81-1223ce0fe33f': 'Open Forum', 
          'c22e8f88-446d-11ee-ad9c-9a734586c732': 'POO Mode Activated 💩', 
          'ca4006b8-f14a-11e9-9b18-0e179a5854dc': 'UPDATE', 
          '35ab95ec-0b14-11e5-87b6-0efd95e46dfd': 'Not the A-hole', 
          '90fe04ea-b1cc-11e3-a793-12313d21c20d': 'Asshole', 
          'ebec91c6-d244-11e8-8071-0e5106890194': 'TL;DR', 
          'cbfad5da-d244-11e8-b3e1-0ef444e90e60': 'No A-holes here', 
          'c122525a-d244-11e8-98e9-0e0449783b98': 'Everyone Sucks', 
          '85ef3c24-464e-11ee-a0e6-f2527a1f87d5': 'Not the A-hole POO Mode', 
          '20701dd2-d245-11e8-99f1-0e2d925c15f4': 'Not enough info'}
# took a gander at the subreddit and POO mode is something they made up for like
# extra moderation of certain posts since sep 2023.
# i can probab;y just lump it in with the regular flairs that aren't POO mode, 
# the judgment is the same regardless
# relevant flairs for me are NTA, YTA, NAH, ESH, and not enough info

# possible features
# title
# body text

# output
# the decision (flair)
# if post has no flair, search for a verdict in top comment (NTA, YTA, ESH, etc.)

def aita_scraper(num_to_scrape = 5, verbose = 0):
    possible_judgments = ["NTA", "YWNBTA", "YTA", "YWBTA", "NAH", "ESH", "INFO"]
    possible_flairs = {'Not the A-hole':"NTA", 
                       "Not the A-hole POO Mode":"NTA",
                       'Asshole':"YTA", 
                       'Asshole POO Mode':"YTA",
                       'No A-holes here':"NAH",
                       'No A-holes here POO Mode':"NAH",
                       'Everyone Sucks':"ESH",
                       'Everyone Sucks POO Mode':"ESH",
                       'Not enough info':"INFO"}
    df = pd.DataFrame(columns = ["title", "post_text", "upvote_percentage", "judgment",
                                 "num_comments", "url", "time_posted", "time_gathered"])
    
    df_index = 0
    for (submission) in (reddit.subreddit('AmItheAsshole').hot(limit=num_to_scrape)):
        if verbose == 1:
            print(">>>Title:", submission.title)
            print(">>>Post:", submission.selftext[0:100])
            print(">>>Upvote percentage:", submission.upvote_ratio * 100)

        flair_text = submission.link_flair_text
        if flair_text != None: #post has flair
            if flair_text in possible_flairs:
                final_judgment = possible_flairs[flair_text]
                if verbose == 1:
                    print("Verdict found:", possible_flairs[flair_text])
                df.loc[df_index, "judgment"] = final_judgment
        
        else: #post doesn't have flair, take top comment
            curr_index = 0
            comment_accessed = False
            while (comment_accessed != True) and (curr_index < len(submission.comments)):
                poster = submission.comments[curr_index].author
                if (poster == None) or (poster.is_mod): # skip comments by mods/bots. 
                    curr_index += 1 
                    # note: not perfect approach as this attribute checks if 
                    # they're a mod of ANY server, not specifically this one but should work OK. 
                    # don't think most general reddit mods are giving opinions here anyway
                else:
                    top_comment_text = submission.comments[curr_index].body
                    if verbose == 1:
                        print(">>>No official verdict yet, top comment:", top_comment_text)
                    
                    judgments_found = 0
                    final_judgment = None
                    for judgment in possible_judgments:
                        if (top_comment_text.find(judgment)) != -1:
                            judgments_found += 1
                            final_judgment = judgment
                    if judgments_found == 1:
                        if verbose == 1:
                            print(">>>Verdict found:", final_judgment)
                        comment_accessed = True
                    else: # no judgment, or multiple found. go to next comment
                        if verbose == 1:
                            print(">>>Undecided on verdict for this comment")
                        curr_index += 1
            df.loc[df_index, "judgment"] = final_judgment
        
        df.loc[df_index, "title"] = submission.title
        df.loc[df_index, "post_text"] = submission.selftext
        df.loc[df_index, "upvote_percentage"] = (submission.upvote_ratio * 100)
        df.loc[df_index, "num_comments"] = submission.num_comments
        df.loc[df_index, "url"] = submission.url
        df.loc[df_index, "time_posted"] = datetime.datetime.fromtimestamp(submission.created_utc)
        df.loc[df_index, "time_gathered"] = datetime.datetime.now()

        df_index += 1

        if verbose == 0.5:
            print(">>>Iteration number:", df_index) 
            print(">>>Current dataframe:")
            print(df)

        with pd.ExcelWriter('/Users/trac.k.y/Documents/pstat131/aita/aita_test.xlsx',
                            engine='xlsxwriter',
                            engine_kwargs={'options': {'strings_to_urls': False}}) as writer:
            df.to_excel(writer, sheet_name = 'test')

    return df

if __name__ == '__main__':
    # constructing and saving database
    aita_result = aita_scraper(1000, verbose = 0.5)
    # max 1000 results at any time. it sucks i know. JUSTICE FOR PUSHSHIFT
    print("Final result:")
    print(aita_result)
    print("Now saving to xlsx file.")
    with pd.ExcelWriter('/Users/trac.k.y/Documents/pstat131/aita/aita_test.xlsx') as writer:
        aita_result.to_excel(writer, sheet_name = 'test')
