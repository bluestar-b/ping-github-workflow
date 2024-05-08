async function fetchDataAndRender() {
  try {
    const response = await fetch('https://raw.githubusercontent.com/bluestar-b/ping-github-workflow/main/pingdata.json');
    const data = await response.json();
    const container = document.getElementById('container');

    for (const key in data) {
      const { description, isUp, time, url, pingTimes } = data[key];
      const card = document.createElement('div');
      card.classList.add('card');
      const status = isUp ? 'Alive' : 'Dead';
      const statusClass = isUp ? 'alive' : 'dead';
      const date = new Date(time);
      const formattedDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;


      card.innerHTML = `
                <div class="description">${description}</div>
                <div>Service: <span class="service-url">${url}</span></div>
                <div>Status: <span class="${statusClass}">${status}</span></div>
                <div>Latency: ${pingTimes[0].responseTime !== null ? pingTimes[0].responseTime + 'ms' : 'N/A'}</div>
                <div>Last checked: ${formattedDate}</div>
            `;
      container.appendChild(card);
    }
  } catch (error) {
    console.error('Failed to fetch and render data:', error);
  }
}

fetchDataAndRender();