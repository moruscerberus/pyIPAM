document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ main.js loaded!');

    // Check if dark mode toggle exists
    const darkToggle = document.getElementById('darkToggle');
    if (darkToggle) {
        console.log('🌗 darkToggle found');
    } else {
        console.log('🌗 darkToggle NOT found');
    }

    // Ensure the search input and filter dropdown exist
    const ipSearch = document.getElementById('ip-search');
    const statusFilter = document.getElementById('status-filter');
    if (ipSearch && statusFilter) {
        console.log('🔍 Filter elements found');
    } else {
        console.log('🔍 Filter elements NOT found');
    }

    // 🌗 DARK MODE TOGGLE
    if (darkToggle) {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme === 'dark') {
            document.body.classList.add('dark-mode');
            darkToggle.textContent = '☀️';
        }

        darkToggle.addEventListener('click', () => {
            const isDark = document.body.classList.toggle('dark-mode');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            darkToggle.textContent = isDark ? '☀️' : '🌙';
        });
    }

    // 🔄 SCAN STATUS POLLING (Optional)
    const scanForm = document.querySelector('form[action*="scan_subnet"]');
    const scanStatus = document.getElementById('scan-status');
    const currentIP = document.getElementById('current-ip');
    const toast = document.getElementById('toast');

    if (scanForm && scanForm.action) {
        const subnetId = scanForm.action.split('/').pop();
        scanForm.addEventListener('submit', () => {
            setTimeout(() => checkScanStatus(subnetId), 1000);
        });
    }

    function checkScanStatus(subnetId) {
        fetch(`/scan_status/${subnetId}`)
            .then(res => res.json())
            .then(data => {
                if (data.scanning) {
                    if (scanStatus) scanStatus.style.display = 'block';
                    if (currentIP) currentIP.innerText = data.current_ip || '';
                    setTimeout(() => checkScanStatus(subnetId), 1000);
                } else {
                    if (scanStatus) scanStatus.style.display = 'none';
                    if (currentIP) currentIP.innerText = '';
                    if (toast) {
                        toast.style.display = 'block';
                        setTimeout(() => toast.style.display = 'none', 3000);
                    }
                }
            });
    }

    // 🔍 SEARCH FILTER (IP or Hostname)
    if (ipSearch || statusFilter) {
        console.log('🔍 Filter elements found');

        const applyFilters = () => {
            const rows = document.querySelectorAll('table tbody tr');
            const searchTerm = ipSearch?.value.toLowerCase() || '';
            const statusTerm = statusFilter?.value.toLowerCase() || '';

            rows.forEach(row => {
                const ip = row.cells[0]?.innerText.toLowerCase();
                const hostname = row.querySelector('input[name="hostname"]')?.value.toLowerCase();
                const status = row.querySelector('select[name="status"]')?.value.toLowerCase();

                const matchesSearch = ip.includes(searchTerm) || hostname.includes(searchTerm);
                const matchesStatus = !statusTerm || status === statusTerm;

                row.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
            });
        };

        if (ipSearch) ipSearch.addEventListener('input', applyFilters);
        if (statusFilter) statusFilter.addEventListener('change', applyFilters);
    }
});
