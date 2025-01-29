# -*- coding: utf-8 -*-

# Standard Modules
import os
import time
from typing import List, Optional

# External Modules
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://www.nogizaka46.com/s/n46/diary/detail/'
NEWEST_URL = f'{BASE_URL}56124?ima=4551&cd=MEMBER'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"
}

def fetch_page_content(url: str) -> str:
    """指定されたURLのページコンテンツを取得する

    Args:
        url (str): 取得するページのURL

    Returns:
        str: ページのHTMLコンテンツ

    Raises:
        requests.HTTPError: HTTPリクエストが失敗した場合
    """
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text

def parse_meta_content(html_content: str, property_name: str) -> str:
    """HTMLコンテンツからメタタグの内容を解析する

    Args:
        html_content (str): 解析するHTMLコンテンツ
        property_name (str): 取得するメタタグのプロパティ名

    Returns:
        str: メタタグの内容。見つからない場合は空文字列
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    meta_tag = soup.find('meta', property=property_name)
    return meta_tag['content'] if meta_tag else ''

def parse_date(html_content: str) -> str:
    """HTMLコンテンツから日付を解析し、フォーマットする

    Args:
        html_content (str): 解析するHTMLコンテンツ

    Returns:
        str: フォーマットされた日付文字列。日付が見つからない場合は空文字列
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    date_tag = soup.find('p', class_='bd--hd__date a--tx js-tdi')
    if not date_tag:
        return ''
    return date_tag.text.strip().replace(':', '：').replace('.', '-').replace(' ', '_')

def extract_image_urls(html_content: str) -> List[str]:
    """HTMLコンテンツから画像URLのリストを抽出する

    Args:
        html_content (str): 解析するHTMLコンテンツ

    Returns:
        List[str]: 抽出された画像URLのリスト
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    return [
        f'https://www.nogizaka46.com{img_tag["src"]}'
        for img_tag in soup.find_all('img')
        if img_tag.get('src') and img_tag['src'].startswith('/')
    ]

def save_images(image_urls: List[str], save_dir: str) -> None:
    """画像URLのリストから画像を保存する

    Args:
        image_urls (List[str]): 保存する画像のURLリスト
        save_dir (str): 画像を保存するディレクトリパス

    Returns:
        None
    """
    os.makedirs(save_dir, exist_ok=True)
    
    for image_url in image_urls:
        image_data = requests.get(image_url).content
        image_name = os.path.join(save_dir, os.path.basename(image_url))
        with open(image_name, 'wb') as image_file:
            image_file.write(image_data)

def save_blog_text(html_content: str, save_dir: str) -> None:
    """ブログ本文をテキストファイルとして保存する

    Args:
        html_content (str): 解析するHTMLコンテンツ
        save_dir (str): テキストファイルを保存するディレクトリパス

    Returns:
        None
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    raw_text = soup.find('div', class_='bd--edit')
    if not raw_text:
        return

    text = '\n'.join(div.get_text() for div in raw_text.find_all('div', dir='auto'))
    if len(text) == 0:
        text = '\n'.join(div.get_text() for div in raw_text.find_all('div'))
    if len(text) == 0:
        text = '\n'.join(div.get_text() for div in raw_text.find_all('p'))
    
    text_path = os.path.join(save_dir, 'blog.txt')
    with open(text_path, 'w', encoding='utf-8') as text_file:
        text_file.write(text)

def find_previous_post_url(html_content: str) -> Optional[str]:
    """前の記事のURLを見つける

    Args:
        html_content (str): 解析するHTMLコンテンツ

    Returns:
        Optional[str]: 前の記事のURL。見つからない場合はNone
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    url_tag = soup.find('a', class_='bd--hn__a hv--op')
    if not url_tag:
        return None

    previous_or_next = url_tag.find('p', class_='bd--hn__tx f--head')
    if not previous_or_next or previous_or_next.text.strip() != '前の記事':
        return None

    return f'https://www.nogizaka46.com{url_tag["href"]}'

def main() -> None:
    """メイン関数：クローリングとスクレイピングのプロセスを調整する

    Returns:
        None
    """
    current_url = NEWEST_URL
    html = fetch_page_content(current_url)
    soup = BeautifulSoup(html, 'html.parser')
    name_tag = soup.find('p', class_='bd--prof__name f--head')
    member_name = name_tag.text.strip().replace(' ', '') if name_tag else 'Unknown'

    post_count = 0
    
    while current_url:
        html = fetch_page_content(current_url)
        title = parse_meta_content(html, 'og:title')
        date = parse_date(html)
        images = extract_image_urls(html)

        save_dir = os.path.join('nogizaka', member_name, f'【{date}】{title}')
        save_images(images, save_dir)
        save_blog_text(html, save_dir)

        post_count += 1
        print(f'取り込み数: {post_count} {current_url}', end='\r', flush=True)

        current_url = find_previous_post_url(html)
        time.sleep(0.1)

    print(f'\n処理完了。合計 {post_count} 件のブログ記事を取得しました。')

if __name__ == "__main__":
    main()