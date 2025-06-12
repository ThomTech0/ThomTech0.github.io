#!/usr/bin/env python3
"""
Script Python pour récupérer toutes les statistiques de traffic d'un dépôt GitHub,
enregistrer les données dans un CSV sans écraser l'existant,
puis produire une page HTML interactive moderne façon Apple.

Ce script utilise l'API GitHub pour obtenir :
  - Clones : détail journalier et totaux
  - Views  : détail journalier et totaux
  - Referrers populaires

Étapes :
1. Récupérer les données et mettre à jour `traffic_data.csv` :
   - Si le fichier existe, n'ajouter que les nouvelles dates.
2. Charger `traffic_data.csv` et la table referrers pour construire le dashboard HTML.
3. Afficher la date de mise à jour du dashboard.

Le dashboard est stylé en CSS épuré, fonds blancs, dégradé violet-rose en fond de page,
couleurs principales du logo. Section "Données journalières" cliquable.

Prérequis :
- Python 3.x
- Les bibliothèques :
    pip install requests pandas plotly jinja2
- Un token GitHub avec le scope `repo` ou `public_repo`, stocké
  dans la variable d'environnement GITHUB_TOKEN.

Usage :
    export GITHUB_TOKEN="votre_token"
    python get_traffic_dashboard.py <owner> <repo>

Exemple :
    python get_traffic_dashboard.py merce-fra PELCA

Résultat :
  - `traffic_data.csv` mis à jour : nouvelles dates ajoutées uniquement
  - `<owner>_<repo>_traffic_dashboard.html` : Dashboard HTML interactif
"""
import os
import sys
import requests
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from jinja2 import Template
from datetime import datetime

# Constantes
IMAGE_URL = (
    'https://github.com/merce-fra/PELCA/raw/'
    'Release_PELCA_v1.3/Images/first_image.png'
)
BASE_API = "https://api.github.com/repos/{owner}/{repo}"
CSV_FILE = 'traffic_data.csv'


def request_json(url: str, token: str) -> dict:
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def fetch_and_update_csv(owner: str, repo: str, token: str) -> pd.DataFrame:
    clones = request_json(f"{BASE_API.format(owner=owner, repo=repo)}/traffic/clones", token).get('clones', [])
    views  = request_json(f"{BASE_API.format(owner=owner, repo=repo)}/traffic/views", token).get('views', [])

    df_cl = pd.DataFrame(clones)
    df_vw = pd.DataFrame(views)
    df_cl['date'] = pd.to_datetime(df_cl['timestamp']).dt.date
    df_vw['date'] = pd.to_datetime(df_vw['timestamp']).dt.date
    df_new = pd.merge(
        df_cl[['date','count','uniques']],
        df_vw[['date','count','uniques']],
        on='date', how='outer', suffixes=('_clones','_views')
    ).sort_values('date')
    df_new.columns = ['date','clones','clones_uniques','views','views_uniques']

    if os.path.exists(CSV_FILE):
        df_exist = pd.read_csv(CSV_FILE, parse_dates=['date'])
        df_exist['date'] = df_exist['date'].dt.date
        mask = ~df_new['date'].isin(df_exist['date'])
        df_append = df_new[mask]
        if not df_append.empty:
            df_updated = pd.concat([df_exist, df_append], ignore_index=True)
            df_updated = df_updated.sort_values('date')
            df_updated.to_csv(CSV_FILE, index=False)
            print(f"Ajout de {len(df_append)} nouvelles lignes au CSV : {CSV_FILE}")
        else:
            df_updated = df_exist
            print("Aucune nouvelle donnée à ajouter au CSV.")
    else:
        df_new.to_csv(CSV_FILE, index=False)
        df_updated = df_new
        print(f"CSV créé avec {len(df_new)} lignes : {CSV_FILE}")

    return df_updated


def fetch_referrers(owner: str, repo: str, token: str) -> pd.DataFrame:
    data = request_json(f"{BASE_API.format(owner=owner, repo=repo)}/traffic/popular/referrers", token)
    return pd.DataFrame(data)


def build_dashboard(owner: str, repo: str, df: pd.DataFrame,
                    df_ref: pd.DataFrame, page_date: str,
                    output_file: str):
    def make_dual(df, y1, y2, title):
        fig = make_subplots(specs=[[{'secondary_y': True}]])
        fig.add_trace(go.Scatter(x=df['date'], y=df[y1], mode='lines+markers',
                                 connectgaps=True, line=dict(shape='linear', color='#8A90C8'), name=y1),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=df['date'], y=df[y2], mode='lines+markers',
                                 connectgaps=True, line=dict(shape='linear', color='#E8B7B7'), name=y2),
                      secondary_y=True)
        fig.update_layout(margin=dict(t=40), title=title, template='simple_white')
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    g1 = make_dual(df, 'clones','clones_uniques', 'Clones vs Visiteurs uniques')
    g2 = make_dual(df, 'views','views_uniques', 'Views vs Visiteurs uniques')

    css = '''
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           color: #333; background: linear-gradient(135deg, #8A90C8 0%, #E8B7B7 100%); }
    .container { max-width: 1200px; margin: auto; padding: 30px;
                 background: #fff; border-radius: 12px;
                 box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
    h1 { text-align: center; color: #4A4A4A; }
    .section { margin-bottom: 40px; }
    .toggle { cursor: pointer; padding: 10px; background: #E8EAF6;
              border-radius: 8px; text-align: center; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; margin-top: 16px; }
    th, td { padding: 10px; border-bottom: 1px solid #ddd; }
    th { background: #F1F3F8; text-align: left; }
    img.header { display: block; margin: 0 auto 25px; max-width: 300px; }
    '''

    tpl = Template(f"""
<!DOCTYPE html>
<html lang='fr'>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width,initial-scale=1'>
  <title>Dashboard {owner}/{repo}</title>
  <style>{css}</style>
  <script>function toggle(){{const c=document.getElementById('daily');c.style.display=c.style.display==='block'?'none':'block';}}</script>
</head>
<body>
  <div class='container'>
    <img class='header' src='{IMAGE_URL}' alt='Logo'>
    <h1>Dashboard {owner}/{repo}</h1>
    <p style='text-align:center;color:#666;'>Page mise à jour le : <strong>{page_date}</strong></p>
    <div class='section'>{g1}</div>
    <div class='section'>{g2}</div>
    <div class='section'><div class='toggle' onclick='toggle()'>Données journalières</div>
      <div id='daily' style='display:none;'>{{{{ df.to_html(index=False, classes='dataframe')|safe }}}}</div></div>
    <div class='section'><h2>Referrers populaires</h2>{{{{ df_ref.to_html(index=False, classes='dataframe')|safe }}}}</div>
  </div>
</body>
</html>
"""
    )
    html = tpl.render(df=df, df_ref=df_ref)
    with open(output_file,'w',encoding='utf-8') as f:
        f.write(html)
    print(f"Dashboard HTML généré : {output_file}")


if __name__=='__main__':
    if len(sys.argv)!=3:
        print("Usage: python get_traffic_dashboard.py <owner> <repo>")
        sys.exit(1)
    owner, repo = sys.argv[1], sys.argv[2]
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Erreur: définir GITHUB_TOKEN")
        sys.exit(1)
    df = fetch_and_update_csv(owner, repo, token)
    df_ref = fetch_referrers(owner, repo, token)
    page_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    out = f"main.html"
    build_dashboard(owner, repo, df, df_ref, page_date, out)
