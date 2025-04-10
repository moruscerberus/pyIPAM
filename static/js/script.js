document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ main.js loaded!');

    // 🌗 DARK MODE TOGGLE
    const darkToggle = document.getElementById('darkToggle');
    if (darkToggle) {
        // Check saved theme preference or use dark mode by default
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme === 'dark' || !storedTheme) {
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
    const ipSearch = document.getElementById('ip-search');
    const statusFilter = document.getElementById('status-filter');
    const resetFiltersButton = document.getElementById('reset-filters');

    if (ipSearch || statusFilter) {
        console.log('🔍 Filter elements found');

        const applyFilters = () => {
            const rows = document.querySelectorAll('table tbody tr');
            const searchTerm = ipSearch?.value.toLowerCase() || '';
            const statusTerm = statusFilter?.value.toLowerCase() || '';
            let visibleCount = 0;

            rows.forEach(row => {
                const ip = row.cells[0]?.innerText.toLowerCase();
                const hostname = row.querySelector('input[name="hostname"]')?.value.toLowerCase();
                const status = row.querySelector('select[name="status"]')?.value.toLowerCase();

                const matchesSearch = ip.includes(searchTerm) || hostname.includes(searchTerm);
                const matchesStatus = !statusTerm || status === statusTerm;

                if (matchesSearch && matchesStatus) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            document.title = `Showing ${visibleCount} results`; // Update page title
        };

        if (ipSearch) ipSearch.addEventListener('input', applyFilters);
        if (statusFilter) statusFilter.addEventListener('change', applyFilters);

        // Reset Filters Button - clear search and filter
        if (resetFiltersButton) {
            resetFiltersButton.addEventListener('click', () => {
                ipSearch.value = '';  // Clear the search field
                statusFilter.value = '';  // Clear the status dropdown
                applyFilters();  // Reapply filters (this will reset everything)
            });
        }
    }
});
