let allTopics = [];

// Função para carregar os tópicos
async function loadTopics() {
    try {
        const response = await fetch('data/index.json');
        allTopics = await response.json();
        document.querySelector('.maintitle').innerText = `:: MANUTENÇÃO & DÚViDAS DETALHADAS :: (${allTopics.length} tópicos)`;
        renderTopicList(allTopics);
    } catch (e) {
        console.error("Erro ao carregar índice:", e);
        // Tentar listar arquivos se o index.json não existir
        renderTopicList([]);
    }
}

function renderTopicList(topics) {
    const tbody = document.querySelector('#topic_list tbody');
    tbody.innerHTML = '';
    
    if (topics.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center;">Nenhum tópico carregado ainda. Verifique se o scraper terminou.</td></tr>';
        return;
    }

    topics.forEach(topic => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><img src="https://www.clubecalibra.com.br/forum/public/style_images/Light345/t_read.png" alt="Read"></td>
            <td>
                <div class="topic_title" onclick="viewTopic('${topic.id}')">${topic.title}</div>
                <div class="desc lighter">Criado por: (veja no tópico)</div>
            </td>
            <td>${topic.messages ? topic.messages.length : 'N/A'}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function viewTopic(topicId) {
    try {
        const response = await fetch(`data/topic_${topicId}.json`);
        const topic = await response.json();
        
        document.querySelector('.category_block').classList.add('hidden');
        document.querySelector('#search_box').classList.add('hidden');
        document.querySelector('#topic_view').classList.remove('hidden');
        
        document.getElementById('current_topic_title').innerText = topic.title;
        const container = document.getElementById('messages_container');
        container.innerHTML = '';
        
        topic.messages.forEach(msg => {
            const post = document.createElement('div');
            post.className = 'post_block';
            post.innerHTML = `
                <div class="author_info">
                    <strong>${msg.author}</strong><br>
                    <span class="desc">Membro</span>
                </div>
                <div class="post_body">
                    <div class="posted_info">Postado em: ${msg.date}</div>
                    <div class="post">${msg.content}</div>
                </div>
            `;
            container.appendChild(post);
        });
        
        window.scrollTo(0, 0);
    } catch (e) {
        alert("Erro ao carregar o tópico!");
    }
}

function showTopicList() {
    document.querySelector('.category_block').classList.remove('hidden');
    document.querySelector('#search_box').classList.remove('hidden');
    document.querySelector('#topic_view').classList.add('hidden');
}

function performSearch() {
    const query = document.getElementById('search_input').value.toLowerCase();
    if (!query) {
        renderTopicList(allTopics);
        return;
    }
    
    const filtered = allTopics.filter(topic => {
        const inTitle = topic.title.toLowerCase().includes(query);
        // Também busca nas mensagens se estiverem carregadas
        const inMessages = topic.messages && topic.messages.some(msg => 
            msg.content.toLowerCase().includes(query) || 
            msg.author.toLowerCase().includes(query)
        );
        return inTitle || inMessages;
    });
    
    renderTopicList(filtered);
}

// Inicializar
document.addEventListener('DOMContentLoaded', loadTopics);
