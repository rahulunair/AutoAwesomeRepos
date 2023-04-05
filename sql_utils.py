import pandas as pd
import sqlite3

from utils import is_relevant_context
from utils import classify_readme
from summary import generate_summary as summary

def export_table_to_csv_pandas(filename):
    """Export repos db to csv."""
    conn = sqlite3.connect("repos.db")
    df = pd.read_sql_query("SELECT * FROM repo_details", conn)
    df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")
    conn.close()

def print_top_k_pandas(k, order_by='stars_count', ascending=False):
    """Print top k records ordered by repos db."""
    conn = sqlite3.connect("repos.db")
    df = pd.read_sql_query("SELECT * FROM repo_details", conn)
    df = df.sort_values(by=order_by, ascending=ascending).head(k)
    print(f"Top {k} records ordered by {order_by}:")
    print(df)
    conn.close()


def create_database_table():
    """Create database table for repo data."""
    conn = sqlite3.connect("repos.db")
    c = conn.cursor()

    # Create repo_details table with default values
    c.execute('''CREATE TABLE IF NOT EXISTS repo_details
                (id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                license TEXT DEFAULT 'Unknown License',
                readme TEXT DEFAULT '',
                stars_count INTEGER DEFAULT 0,
                forks_count INTEGER DEFAULT 0,
                pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                languages TEXT DEFAULT '',
                topics TEXT DEFAULT '',
                open_issues INTEGER DEFAULT 0,
                closed_issues INTEGER DEFAULT 0,
                description TEXT DEFAULT '',
                fork INTEGER DEFAULT 0,
                size INTEGER DEFAULT 0,
                watchers_count INTEGER DEFAULT 0,
                language TEXT DEFAULT '',
                keyword TEXT DEFAULT '',
                additional_keywords TEXT DEFAULT '',
                is_relevant INTEGER DEFAULT NULL,
                brief_desc TEXT DEFAULT NULL,
                class_label TEXT DEFAULT NULL,
                fetch_data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()
"""
def save_results_to_db(repos):
    create_database_table()
    conn = sqlite3.connect("repos.db")
    c = conn.cursor()
    for repo_info in repos:
        print(f"repo_info: {repo_info}")
        c.execute('''
            INSERT INTO repo_details (
                id, url, license, readme, stars_count, forks_count, pushed_at, updated_at, created_at, languages, topics,
                open_issues, closed_issues, description, fork, size,
                watchers_count, language, keyword, additional_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)''', (
            repo_info.id, repo_info.url, repo_info.license,repo_info.readme, repo_info.stars_count, repo_info.forks_count,
            repo_info.pushed_at, repo_info.updated_at, repo_info.created_at, repo_info.languages, ','.join(repo_info.topics),
            repo_info.open_issues, repo_info.closed_issues,repo_info.description, repo_info.fork, 
            repo_info.size, repo_info.watchers_count, repo_info.language,
            repo_info.keyword, ','.join(repo_info.additional_keywords)
        ))

    conn.commit()
    conn.close()
""" 

def save_results_to_db(repos):
    """Save repo data to database."""
    create_database_table()
    conn = sqlite3.connect("repos.db")

    data = []
    for repo_info in repos:
        data.append((
            repo_info.id, repo_info.url, repo_info.license, repo_info.readme, repo_info.stars_count, repo_info.forks_count,
            repo_info.pushed_at, repo_info.updated_at, repo_info.created_at, repo_info.languages, '|`'.join(repo_info.topics),
            repo_info.open_issues, repo_info.closed_issues, repo_info.description, repo_info.fork,
            repo_info.size, repo_info.watchers_count, repo_info.language,
            repo_info.keyword, ','.join(repo_info.additional_keywords)
        ))
    
    df = pd.DataFrame(data, columns=[
        'id', 'url', 'license', 'readme', 'stars_count', 'forks_count', 'pushed_at', 'updated_at', 'created_at', 'languages', 'topics',
        'open_issues', 'closed_issues', 'description', 'fork', 'size', 'watchers_count', 'language', 'keyword', 'additional_keywords'
    ])

    df.to_sql('repo_details', conn, if_exists='append', index=False)
    conn.close()


def process_repo_details():
    """Process repo details and update database table."""
    conn = sqlite3.connect("repos.db")
    df = pd.read_sql_query("SELECT * FROM repo_details WHERE class_label IS NULL", conn)
    df['is_relevant'] = df.apply(lambda row: is_relevant_context(row['readme'], row['keyword']), axis=1)
    df['brief_desc'] = df['readme'].apply(lambda x: summary(x, use_openai=True))
    df['class_label'] = df.apply(lambda row: classify_readme(readme=row['readme'], readme_summary=row['brief_desc'], use_openai=True), axis=1)
    df.to_sql('repo_details', conn, if_exists='replace', index=False)
    conn.close()


if __name__ == "__main__":
    export_table_to_csv_pandas("./results/repos.csv")
    print_top_k_pandas(10, order_by='stars_count', ascending=False)
    #process_repo_details()