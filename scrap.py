from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import re

url = ('http://www.imdb.com/search/title?count=200&view=simple&boxoffice_gross_us=1,&title_type=feature&release_date={year}')

headers = {
    'Accept-Language': 'en-US',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }


def get_movies(year):
    '''Get list of movies released in <year>.'''
    movies_html = requests.get(url.format(year=year), headers=headers).content
    soup = BeautifulSoup(movies_html, 'html.parser')
    movies = soup.find_all('a', href=re.compile('adv_li_tt'))

    return ['http://www.imdb.com' + m['href'] for m in movies]


def go_to_movie(url):
    '''Get IMDb page of a movie.'''
    movie_html = requests.get(url, headers=headers).content

    return movie_html


def get_name(soup):
    try:
        name = soup.find('h1').text.strip()
    except AttributeError:
        return None

    return name


def get_genre(soup):
    try:
        genre = soup.find('a', href=re.compile('tt_ov_inf')).text
    except AttributeError:
        return None

    return genre


def get_votes(soup):
    try:
        wrapper = soup.find('a', href=re.compile('tt_ov_rt')).text
        try:
            if wrapper[-1] == "M":
                votes = float(wrapper[6:-1])*1000000
            elif wrapper[-1] == "K":
                votes = float(wrapper[6:-1])*1000
            else:
                votes = float(int(wrapper[6]))
        except ValueError:
            return None
    except AttributeError:
        return None

    return votes


def get_money(soup, type):
    try:
        wrapper = soup.find('span', text=type).findNext('div')
        money = wrapper.find('span').text
    except AttributeError:
        return None

    return money


def get_company(soup):
    try:
        wrapper = soup.find('a', text='Production companies')
        if not wrapper:
            wrapper = soup.find('span', text='Production company')
        if not wrapper:
            wrapper = soup.find('a', text='Production company')
        company = wrapper.findNext('div').find('a').text
    except AttributeError:
        return None

    return company


def get_release_date(soup):
    try:
        wrapper = soup.find('a', text='Release date').findNext('div')
        release_date = wrapper.find('a').text
    except AttributeError:
        return None

    return release_date


def get_rating(soup):
    try:
        rating = soup.find('a', {'href': re.compile('tt_ov_pg')}).text
    except AttributeError:
        return None

    return rating


def get_runtime(soup):
    try:
        wrapper = soup.find('span', text='Runtime').findNext('div').text.split()
        if len(wrapper) == 4:
            hours = int(wrapper[0]) * 60
            minutes = int(wrapper[2])
            runtime = hours + minutes
        elif 'hours' in wrapper[1]:
            runtime = int(wrapper[0]) * 60
        elif 'minutes' in wrapper[1]:
            runtime = int(wrapper[0])
    except AttributeError:
        return None

    return runtime


def get_star(soup):
    try:
        wrapper = soup.find('a', text='Stars')
    except AttributeError:
        return None
    
    if not wrapper:
        wrapper = soup.find('span', text='Stars')
        
    try:
        wrapper = wrapper.findNext('div')
    except AttributeError:
        return None
    
    try:
        star = wrapper.find('a').text
    except AttributeError:
        return None
    
    return star


def get_writer(soup):
    try:
        writer = soup.find('a', {'href': re.compile('tt_ov_wr')}).text
    except AttributeError:
        return None
    
    if writer == 'Writers':
        try:
            wrapper = soup.find('a', text='Writers').findNext('div')
        except AttributeError:
            wrapper = soup.find('span', text='Writers').findNext('div') 
        writer = wrapper.find('a').text

    return writer


def get_director(soup):
    try:
        director = soup.find('a', {'href': re.compile('tt_ov_dr')}).text
    except AttributeError:
        return None
    
    return director


def get_country(soup):
    try:
        wrapper = soup.find('span', text='Country of origin')
        if not wrapper:
            wrapper = soup.find('span', text='Countries of origin')
        country = wrapper.findNext('div').find('a').text
    except AttributeError:
        return None

    return country


def get_score(soup):
    try:
        score = soup.find('div', attrs={'data-testid' : "hero-rating-bar__aggregate-rating__score"}).findNext('span').text
    except AttributeError:
        score = None

    return score


def scrap_titlebar(soup, year):
    '''Get name, rating, genre, year, release date, score and votes of a movie.'''
    print(year)
    name     = get_name(soup)
    print(name)
    genre    = get_genre(soup)
    score    = get_score(soup)
    votes    = get_votes(soup)
    released = get_release_date(soup)
    rating   = get_rating(soup)

    titlebar = {
        'name': name,
        'rating': rating,
        'genre': genre,
        'year': year,
        'released': released,
        'score': score,
        'votes': votes
    }

    return titlebar


def scrap_crew(soup):
    '''Get director, writer and star of a movie.'''
    director = get_director(soup)
    writer   = get_writer(soup)
    star     = get_star(soup)

    crew = {
        'director': director,
        'writer': writer,
        'star': star
    }

    return crew


def scrap_details(soup):
    '''Get country, budget, gross, production co. and runtime of a movie.'''
    country = get_country(soup)
    gross   = get_money(soup, type='Gross worldwide')
    budget  = get_money(soup, type='Budget')
    company = get_company(soup)
    runtime = get_runtime(soup)

    if budget:
        if not '$' in budget:
            budget = None
        else:
            try:
                budget = float(budget.split()[0].replace('$','').replace(',',''))
            except ValueError:
                budget = None

    if gross:
        gross = float(gross.replace('$','').replace(',',''))

    details = {
        'country': country,
        'budget': budget,
        'gross': gross,
        'company': company,
        'runtime': runtime
    }

    return details


def write_csv(data):
    '''Write list of dicts to csv.'''
    df = pd.DataFrame(data)
    df.to_csv('imdb.csv', index=False)


def main():
    all_movie_data = []

    for year in range(1970, 2021):
        movies = get_movies(year)
        
        for movie_url in movies:
            movie_data = {}
            movie_html = go_to_movie(movie_url)
            
            soup = BeautifulSoup(movie_html, 'html.parser')
            
            movie_data.update(scrap_titlebar(soup, year))
            movie_data.update(scrap_crew(soup))
            movie_data.update(scrap_details(soup))
            
            all_movie_data.append(movie_data)
            #time.sleep(1)        
            # df = pd.DataFrame(all_movie_data)
            # df.to_csv('movies_{}.csv'.format(year), sep=',', index=False)

        print(year, 'done.')

    write_csv(all_movie_data)


if __name__ == '__main__':
    main()
