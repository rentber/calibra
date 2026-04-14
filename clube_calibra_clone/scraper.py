import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re

# Configurações
BASE_URL = "https://www.clubecalibra.com.br/forum/"
FORUM_URL = f"{BASE_URL}forum/5-manutencao-duvidas-detalhadas/"
LOGIN_URL = f"{BASE_URL}index.php?app=core&module=global&section=login"
LOGIN_PROCESS_URL = f"{BASE_URL}index.php?app=core&module=global&section=login&do=process"

USERNAME = "renato"
PASSWORD = "loreta"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

def is_logged_in(html_content):
    """Verifica se o HTML contém indícios de que o usuário está logado."""
    return "Sair" in html_content or USERNAME in html_content.lower()

def login():
    print("Tentando fazer login...")
    try:
        # 1. Pegar a página de login para obter o auth_key se necessário
        r = session.get(LOGIN_URL, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Procurar por auth_key
        auth_key_input = soup.find('input', {'name': 'auth_key'})
        auth_key = auth_key_input['value'] if auth_key_input else ""
        
        payload = {
            'ips_username': USERNAME,
            'ips_password': PASSWORD,
            'auth_key': auth_key,
            'rememberMe': '1',
            'referer': FORUM_URL,
            'return': '1'
        }
        
        r = session.post(LOGIN_PROCESS_URL, data=payload, timeout=15)
        
        if is_logged_in(r.text) or "Você está logado" in r.text:
            print("Login realizado com sucesso!")
            return True
        else:
            print("Falha no login. Verifique as credenciais.")
            with open("login_debug.html", "w", encoding="utf-8") as f:
                f.write(r.text)
            return False
    except Exception as e:
        print(f"Erro durante o login: {e}")
        return False

def check_auth_and_get(url):
    """Faz um GET e verifica se ainda está logado. Se não, tenta relogar."""
    try:
        r = session.get(url, timeout=15)
        if not is_logged_in(r.text):
            print("Sessão expirada. Tentando relogar...")
            if login():
                r = session.get(url, timeout=15)
            else:
                print("Não foi possível relogar.")
        return r
    except Exception as e:
        print(f"Erro na requisição para {url}: {e}")
        return None

def get_topics():
    print("Obtendo lista de tópicos...")
    topics = []
    page = 1
    
    while True:
        url = f"{FORUM_URL}page-{page}" if page > 1 else FORUM_URL
        print(f"Lendo página {page} de tópicos...")
        r = check_auth_and_get(url)
        if not r: break
        
        soup = BeautifulSoup(r.content, 'html.parser')
        topic_links = soup.select('a.topic_title')
        
        if not topic_links:
            break
            
        for link in topic_links:
            topics.append({
                'title': link.text.strip(),
                'url': link['href'],
                'id': re.search(r'topic/(\d+)-', link['href']).group(1) if re.search(r'topic/(\d+)-', link['href']) else "unknown"
            })
            
        next_page = soup.select_one('li.next a')
        if not next_page: # Removido o limite de páginas para clonar TODO o fórum
            break
        page += 1
        time.sleep(1)
        
    return topics

def get_messages(topic_url):
    print(f"Lendo mensagens de: {topic_url}")
    messages = []
    page = 1
    
    while True:
        url = f"{topic_url}page-{page}" if page > 1 else topic_url
        r = check_auth_and_get(url)
        if not r: break
        
        soup = BeautifulSoup(r.content, 'html.parser')
        posts = soup.select('div.post_block')
        if not posts:
            break
            
        for post in posts:
            author = post.select_one('span.author.vcard')
            content = post.select_one('div.post_body div.post')
            date = post.select_one('abbr.published')
            
            messages.append({
                'author': author.text.strip() if author else "Anônimo",
                'date': date['title'] if date and date.has_attr('title') else (date.text.strip() if date else "Data desconhecida"),
                'content': str(content) if content else ""
            })
            
        next_page = soup.select_one('li.next a')
        if not next_page:
            break
        page += 1
        time.sleep(0.5)
        
    return messages

def main():
    if not login():
        return
        
    if not os.path.exists('data'):
        os.makedirs('data')

    topics = get_topics()
    print(f"Total de tópicos encontrados: {len(topics)}")
    
    # Carregar dados existentes para não re-baixar tudo
    all_data = []
    if os.path.exists('data/index.json'):
        try:
            with open('data/index.json', 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            print("Aviso: data/index.json corrompido. Tentando reconstruir a partir de arquivos individuais...")
            # Reconstruir a partir dos arquivos topic_*.json
            for file in os.listdir('data'):
                if file.startswith('topic_') and file.endswith('.json'):
                    try:
                        with open(os.path.join('data', file), 'r', encoding='utf-8') as f:
                            all_data.append(json.load(f))
                    except:
                        pass
    
    existing_ids = {str(t['id']) for t in all_data}
    
    for i, topic in enumerate(topics):
        topic_id = topic['id']
        if topic_id in existing_ids:
            print(f"Pulando tópico {topic_id} (já baixado)")
            continue

        print(f"Processando tópico {i+1}/{len(topics)}: {topic['title']}")
        topic['messages'] = get_messages(topic['url'])
        all_data.append(topic)
        
        # Salvar individualmente
        with open(f"data/topic_{topic_id}.json", "w", encoding="utf-8") as f:
            json.dump(topic, f, ensure_ascii=False, indent=4)
            
        # Atualizar índice geral
        with open("data/index.json", "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
            
        time.sleep(1)
    
    print("Processo concluído com sucesso!")
    with open("done.txt", "w") as f:
        f.write("FINISHED")

if __name__ == "__main__":
    main()
