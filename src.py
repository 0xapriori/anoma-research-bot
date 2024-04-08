
import tweepy
import requests
from bs4 import BeautifulSoup
import time
import os
import anthropic


consumer_key = os.environ['']
consumer_secret = os.environ['']
access_token = os.environ['']
access_token_secret = os.environ['']
anthropic.setup(api_key = os.environ[''])

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

def scrape_new_posts():
    url = "https://research.anoma.net"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    posts = soup.find_all("div", class_="post")
    new_posts = []

    for post in posts:
        title = post.find("h2").text
        link = post.find("a")["href"]
        content = post.find("div", class_="post-content").text

        if is_new_post(title):
            new_posts.append({"title": title, "link": link, "content": content})

    return new_posts

def is_new_post(title):
    processed_titles_file = "processed_titles.txt"

    if not os.path.exists(processed_titles_file):
        return True

    with open(processed_titles_file, "r") as file:
        processed_titles = file.read().splitlines()

    if title in processed_titles:
        return False

    with open(processed_titles_file, "a") as file:
        file.write(title + "\n")

    return True

def generate_tldr_summary(content):
    response = anthropic.completion(
        model="claude-v1",
        prompt=f"Generate a 2-line TL;DR summary of the following text:\n\n{content}",
        max_tokens_to_sample=50,
        temperature=0.7,
    )
    summary = response.result["completionText"]
    return summary

def generate_eli5_explanation(content):
    response = anthropic.completion(
        model="claude-v1",
        prompt=f"Explain the following text like I'm 5 years old:\n\n{content}",
        max_tokens_to_sample=100,
        temperature=0.7,
    )
    explanation = response.result["completionText"]
    return explanation

def post_to_twitter(title, link, tldr_summary, eli5_explanation):
    tweet = f"{tldr_summary}\n\n{eli5_explanation}\n\n{link}"
    try:
        api.update_status(tweet)
        print(f"Tweeted: {tweet}")
    except tweepy.TweepError as e:
        print(f"Error posting tweet: {str(e)}")

def main():
    while True:
        try:
            new_posts = scrape_new_posts()
            for post in new_posts:
                tldr_summary = generate_tldr_summary(post["content"])
                eli5_explanation = generate_eli5_explanation(post["content"])
                post_to_twitter(post["title"], post["link"], tldr_summary, eli5_explanation)
        except Exception as e:
            print(f"Error: {str(e)}")

        time.sleep(3600)  # Wait for 1 hour before checking for new posts again

if __name__ == "__main__":
    main()
