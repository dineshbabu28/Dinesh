import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_option_menu import option_menu
import streamlit as st
import pymongo
import pymysql
from  pymongo import MongoClient
import mysql.connector as sql
from googleapiclient.discovery import build
from PIL import Image
import time

# SETTING PAGE CONFIGURATIONS
st.set_page_config(page_title= "Youtube Data Harvesting and Warehousing",
                   layout= "wide",
                   initial_sidebar_state= "expanded")

# CREATING OPTION MENU
with st.sidebar:
    selected = option_menu(None, ["Home","Extract & Transform","View"], 
                           icons=["house-door-fill","tools","card-text"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "30px", "text-align": "centre", "margin": "0px", 
                                                "--hover-color": "#C80101"},
                                   "icon": {"font-size": "30px"},
                                   "container" : {"max-width": "6000px"},
                                   "nav-link-selected": {"background-color": "#C80101"}})
# Bridging a connection with MongoDB Atlas and Creating a new database(youtube_data)
cluster= MongoClient("mongodb+srv://vdineshrvd97:dineshsubbu28@cluster0.bqk6tu5.mongodb.net/?retryWrites=true&w=majority")
db=cluster.DS

# CONNECTING WITH MYSQL DATABASE
import sqlite3
mydb=sqlite3.connect('C:\\Work\\Python\\YoutubeData\\DS.db')
mycursor=mydb.cursor()

# BUILDING CONNECTION WITH YOUTUBE API
api_key = "AIzaSyC9lK5JiTsTcRPq121wKccpM6CiJe5CRgg" #"AIzaSyAc5yh9GIFfaop4yMixH2KVqHZGuKpEAWU" 
youtube = build('youtube','v3',developerKey=api_key)


# FUNCTION TO GET CHANNEL DETAILS
def get_channel_details(channel_id):
    ch_data = []
    response = youtube.channels().list(part = 'snippet,contentDetails,statistics',
                                     id= channel_id).execute()

    for i in range(len(response['items'])):
        data = dict(Channel_id = channel_id[i],
                    Channel_name = response['items'][i]['snippet']['title'],
                    Playlist_id = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'],
                    Subscribers = response['items'][i]['statistics']['subscriberCount'],
                    Views = response['items'][i]['statistics']['viewCount'],
                    Total_videos = response['items'][i]['statistics']['videoCount'],
                    Description = response['items'][i]['snippet']['description'],
                    Country = response['items'][i]['snippet'].get('country')
                    )
        ch_data.append(data)
    return ch_data

# FUNCTION TO GET VIDEO IDS
def get_channel_videos(channel_id):
    video_ids = []
    # get Uploads playlist id
    res = youtube.channels().list(id=channel_id, 
                                  part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    
    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id, 
                                           part='snippet', 
                                           maxResults=50,
                                           pageToken=next_page_token).execute()
        
        for i in range(len(res['items'])):
            video_ids.append(res['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = res.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_ids


# FUNCTION TO GET VIDEO DETAILS
def get_video_details(v_ids):
    video_stats = []
    
    for i in range(0, len(v_ids), 50):
        response = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(v_ids[i:i+50])).execute()
        for video in response['items']:
            video_details = dict(Channel_name = video['snippet']['channelTitle'],
                                Channel_id = video['snippet']['channelId'],
                                Video_id = video['id'],
                                Title = video['snippet']['title'],
                                Tags = video['snippet'].get('tags'),
                                Thumbnail = video['snippet']['thumbnails']['default']['url'],
                                video_description = video['snippet']['description'],
                                Published_date = video['snippet']['publishedAt'],
                                duration = video['contentDetails']['duration'],
                                view_count = video['statistics']['viewCount'],
                                like_count = video['statistics'].get('likeCount'),
                                comment_count = video['statistics'].get('commentCount'),
                                Favorite_count = video['statistics']['favoriteCount'],
                                Definition = video['contentDetails']['definition'],
                                Caption_status = video['contentDetails']['caption']
                               )
            video_stats.append(video_details)
    return video_stats


# FUNCTION TO GET COMMENT DETAILS
def get_comments_details(v_id):
    comment_data = []
    try:
        next_page_token = None
        while True:
            response = youtube.commentThreads().list(part="snippet,replies",
                                                    videoId=v_id,
                                                    maxResults=100,
                                                    pageToken=next_page_token).execute()
            for cmt in response['items']:
                data = dict(Comment_id = cmt['id'],
                            Video_id = cmt['snippet']['videoId'],
                            Comment_text = cmt['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_author = cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            comment_published_date = cmt['snippet']['topLevelComment']['snippet']['publishedAt'],
                            Like_count = cmt['snippet']['topLevelComment']['snippet']['likeCount'],
                            Reply_count = cmt['snippet']['totalReplyCount']
                           )
                comment_data.append(data)
            next_page_token = response.get('nextPageToken')
            if next_page_token is None:
                break
    except:
        pass
    return comment_data


# FUNCTION TO GET CHANNEL NAMES FROM MONGODB
def channel_names():   
    ch_name = []
    for i in db.channel_details.find():
        ch_name.append(i['Channel_name'])
    return ch_name


# HOME PAGE
if selected == "Home":
    # Title Image
    col1,col2 = st.columns(2,gap= 'medium')
    col1.markdown("## :blue[Domain] : Social Media")
    col1.markdown("## :blue[Technologies used] : Python,MongoDB, Youtube Data API, MySql, Streamlit")
    col1.markdown("## :blue[Overview] : Retrieving the Youtube channels data from the Google API, storing it in a MongoDB as data lake, migrating and transforming data into a SQL database,then querying the data and displaying it in the Streamlit app.")
    col2.markdown("#   ")
    col2.markdown("#   ")
    col2.markdown("#   ")

    
    
# EXTRACT AND TRANSFORM PAGE
if selected == "Extract & Transform":
    tab1, tab2 = st.tabs(["$\huge 📝 EXTRACT $", "$\huge🚀 TRANSFORM $"])
    
    # EXTRACT TAB
    with tab1:
        st.markdown("#    ")
        st.write("### Enter YouTube Channel_ID below :")
        ch_id = st.text_input("Hint : Goto channel's home page > Right click > View page source > Find channel_id").split(',')

        if ch_id and st.button("Extract Data"):
            ch_details = get_channel_details(ch_id)
            st.write(f'#### Extracted data from :green["{ch_details[0]["Channel_name"]}"] channel')
            st.table(ch_details)

        if st.button("Upload to MongoDB"):
            with st.spinner('Please Wait for it...'):
                ch_details = get_channel_details(ch_id)
                v_ids = get_channel_videos(ch_id)
                vid_details = get_video_details(v_ids)
                
                def comments():
                    com_d = []
                    for i in v_ids:
                        com_d += get_comments_details(i)
                    return com_d
                
                comm_details = comments()

                collections1 = db.channel_details
                collections1.insert_many(ch_details)

                collections2 = db.video_details
                collections2.insert_many(vid_details)

                collections3 = db.comments_details
                collections3.insert_many(comm_details)
                st.success("Upload to MongoDB successful !!")
   
   # TRANSFORM TAB
    with tab2:     
     st.markdown("#   ")
     st.markdown("### Select a channel to begin Transformation to SQL")
     ch_names = channel_names()  
     user_inp = st.selectbox("Select channel", options=ch_names)

# Insert into Channels table
#def insert_into_channels():
    collections1 = db.channel_details
    
    for i in collections1.find({"Channel_name": user_inp}, {'_id': 0}):
        query = "INSERT INTO channels (Channel_id, Channel_name, Playlist_id, Subscribers, Views, Total_videos, Description, Country) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
            i.get('Channel_id', ''), i.get('Channel_name', ''), i.get('Playlist_id', ''), 
            i.get('Subscribers', ''), i.get('Views', ''), i.get('Total_videos', ''), 
            i.get('Description', ''), i.get('Country', '')
        )
        try:
            mycursor.execute(query)
            mydb.commit()
            print("Channels Insertion successful!")
        except Exception as e:
            print(f"Error inserting channels: {e}")
            mydb.rollback()  # Rollback the transaction in case of an error
            time.sleep(1) 
            continue
# Insert into Videos table
#def insert_into_videos():
    collections2 = db.video_details
    
    for i in collections2.find({"Channel_name": user_inp}, {'_id': 0}):
        query = "INSERT INTO videos (Video_id,Channel_id,Title,video_description,Published_date,Channel_name,Caption_status,view_count,like_count,comment_count,duration,Favorite_count) " \
                "VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
            i.get('Video_id', ''),i.get('Channel_id', ''),i.get('Title', ''),i.get('video_description', ''),i.get('Published_date', ''),i.get('Channel_name', ''),
            i.get('Caption_status', ''),i.get('view_count', ''),i.get('like_count', ''),i.get('comment_count', ''),i.get('duration', ''),i.get('Favorite_count', '')

        )
        try:
            mycursor.execute(query)
            mydb.commit()
            print("Videos Insertion successful!")
        except Exception as e:
            print(f"Error inserting videos: {e}")
            mydb.rollback()  # Rollback the transaction in case of an error
            time.sleep(1)  # Wait for 1 second before retrying
            continue  #
# Insert into Comments table
def insert_into_comments():
    collections1 = db.video_details
    collections2 = db.comments_details

    for vid in collections1.find({"Channel_name": user_inp}, {'_id': 0}):
        for i in collections2.find({'Video_id': vid.get('Video_id', '')}, {'_id': 0}):
            query2 = "INSERT INTO comments (Comment_id, Video_id, Comment_author, Comment_text, comment_published_date) " \
                     "VALUES ('{}', '{}', '{}', '{}', '{}')".format(
                i.get('Comment_id', ''), i.get('Video_id', ''), i.get('Comment_author', ''),
                i.get('Comment_text', ''), i.get('comment_published_date', '')
            )
            try:
                mycursor.execute(query2)
                mydb.commit()
                print("Comments Insertion successful!")
            except Exception as e:
                print(f"Error inserting comments: {e}")
                mydb.rollback()  # Rollback the transaction in case of an error
        
if st.button("Submit"):
    try:
        insert_into_comments()
        st.success("Transformation to MySQL Successful !!")
    except Exception as e:
        st.error(f"Error: {e}")
# VIEW PAGE
if selected == "View":
    
    st.write("## :orange[Select any question to get Insights]")
    questions = st.selectbox('Questions',
    ['1. What are the names of all the videos and their corresponding channels?',
    '2. Which channels have the most number of videos, and how many videos do they have?',
    '3. What are the top 10 most viewed videos and their respective channels?',
    '4. How many comments were made on each video, and what are their corresponding video names?',
    '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
    '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
    '7. What is the total number of views for each channel, and what are their corresponding channel names?',
    '8. What are the names of all the channels that have published videos in the year 2022?',
    '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
    '10. Which videos have the highest number of comments, and what are their corresponding channel names?'])
    
    if questions == '1. What are the names of all the videos and their corresponding channels?':
        mycursor.execute("""SELECT title AS Video_Title, channel_name AS Channel_Name
                            FROM videos
                            ORDER BY channel_name""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)
        st.write(df)
        
    elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, total_videos AS Total_Videos
                            FROM channels
                            ORDER BY total_videos DESC""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)
        st.write(df)
        st.write("### :green[Number of videos in each channel :]")
        #st.bar_chart(df,x= mycursor.column_names[0],y= mycursor.column_names[1])
        fig = px.bar(df,
                 x='Channel_Name',
                 y='Total_Videos',
                 orientation='v',
                 color='Channel_Name')
        st.plotly_chart(fig, use_container_width=True)
        
    elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, title AS Video_Title, views AS Views 
                            FROM videos
                            ORDER BY views DESC
                            LIMIT 10""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)
        st.write(df)
        st.write("### :green[Top 10 most viewed videos :]")
        fig = px.bar(df,
                 x='Views',
                 y='Video_Title',
                 orientation='h',
                 color='Channel_Name')
        st.plotly_chart(fig, use_container_width=True)
        
    elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
        mycursor.execute("""SELECT a.video_id AS Video_id, a.title AS Video_Title, b.Total_Comments
                            FROM videos AS a
                            LEFT JOIN (SELECT video_id,COUNT(comment_id) AS Total_Comments
                            FROM comments GROUP BY video_id) AS b
                            ON a.video_id = b.video_id
                            ORDER BY b.Total_Comments DESC""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)
        st.write(df)
          
    elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name,title AS Title,likes AS Likes_Count 
                            FROM videos
                            ORDER BY likes DESC
                            LIMIT 10""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)
        st.write(df)
        st.write("### :green[Top 10 most liked videos :]")
        fig = px.bar(df,
                 x='Likes_Count',
                 y='Title',
                 orientation='h',
                 color='Channel_Name')
        st.plotly_chart(fig, use_container_width=True)
        
    elif questions == '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
        mycursor.execute("""SELECT title AS Title, likes AS Likes_Count
                            FROM videos
                            ORDER BY likes DESC""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)
        st.write(df)
         
    elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, views AS Views
                            FROM channels
                            ORDER BY views DESC""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)  
        st.write(df)
        st.write("### :green[Channels vs Views :]")
        fig = px.bar(df,
                 x='Channel_Name',
                 y='Views',
                 orientation='v',
                 color='Channel_Name')
        st.plotly_chart(fig, use_container_width=True)
        
    elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
        mycursor.execute("""SELECT channel_name AS Channel_Name
                            FROM videos
                            WHERE published_date LIKE '2022%'
                            GROUP BY channel_name
                            ORDER BY channel_name""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)
        st.write(df)
        
    elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name,
                            AVG(duration)/60 AS "Average_Video_Duration (mins)"
                            FROM videos
                            GROUP BY channel_name
                            ORDER BY AVG(duration)/60 DESC""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)  
        st.write(df)
        st.write("### :green[Avg video duration for channels :]")
        fig = px.bar(df,
                 x='Channel_Name',
                 y='Average_Video_Duration (mins)',
                 orientation='v',
                 color='Channel_Name')
        st.plotly_chart(fig, use_container_width=True)
        
    elif questions == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name,video_id AS Video_ID,comments AS Comments
                            FROM videos
                            ORDER BY comments DESC
                            LIMIT 10""")
        column_names = [description[0] for description in mycursor.description]
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=column_names)   
        st.write(df)
        st.write("### :green[Videos with most comments :]")
        fig = px.bar(df,
                 x='Comments',
                 y='Video_ID',
                 orientation='h',
                 color='Channel_Name')
        st.plotly_chart(fig, use_container_width=True)
