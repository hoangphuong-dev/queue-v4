// Trong file static/src/js/route_graph_static.js
(function () {
    "use strict";

    // Đợi DOM sẵn sàng
    document.addEventListener('DOMContentLoaded', function () {
        loadData();

        // Xử lý nút làm mới
        document.getElementById('btn-refresh').addEventListener('click', loadData);
    });

    // Hàm tải dữ liệu
    function loadData() {
        showLoading(true);

        // Lấy danh sách nhóm dịch vụ
        fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': readCookie('csrf_token'),
            },
            body: JSON.stringify({
                params: {
                    model: 'queue.service.group',
                    method: 'search_read',
                    args: [[], ['name', 'code', 'sequence']],
                    kwargs: {},
                },
            }),
        })
            .then(response => response.json())
            .then(groupsData => {
                const groups = groupsData.result;

                // Lấy dữ liệu tuyến đường
                return fetch('/web/dataset/call_kw', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': readCookie('csrf_token'),
                    },
                    body: JSON.stringify({
                        params: {
                            model: 'queue.service.group.route',
                            method: 'get_route_visualization_data',
                            args: [],
                            kwargs: {},
                        },
                    }),
                })
                    .then(response => response.json())
                    .then(routesData => {
                        const routes = routesData.result;

                        showLoading(false);

                        if (groups.length === 0 || routes.length === 0) {
                            document.getElementById('no-data-message').classList.remove('d-none');
                        } else {
                            document.getElementById('no-data-message').classList.add('d-none');
                            renderGraph(groups, routes);
                        }
                    });
            })
            .catch(error => {
                console.error("Lỗi khi tải dữ liệu tuyến đường:", error);
                showLoading(false);
                alert("Không thể tải dữ liệu tuyến đường. Vui lòng thử lại sau.");
            });
    }

    // Hiển thị/ẩn loading
    function showLoading(show) {
        if (show) {
            document.getElementById('loading').classList.remove('d-none');
            document.getElementById('content').classList.add('d-none');
        } else {
            document.getElementById('loading').classList.add('d-none');
            document.getElementById('content').classList.remove('d-none');
        }
    }

    // Vẽ đồ thị
    function renderGraph(groups, routes) {
        const svgContainer = document.getElementById('svg-container');
        svgContainer.innerHTML = ''; // Xóa nội dung cũ

        const width = svgContainer.clientWidth || 800;
        const height = 500;

        // Tạo SVG container
        const xmlns = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(xmlns, "svg");
        svg.setAttribute("width", width);
        svg.setAttribute("height", height);
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svgContainer.appendChild(svg);

        // Tính toán vị trí cho các node
        const nodeRadius = 60;
        const nodeSpacing = 200;
        const startX = 120;
        const startY = height / 2;

        // Vẽ các node (nhóm dịch vụ)
        const nodePositions = {};

        groups.forEach((group, index) => {
            const x = startX + (index * nodeSpacing);
            const y = startY;

            // Lưu vị trí của node để sử dụng khi vẽ đường nối
            nodePositions[group.id] = { x, y };

            // Vẽ node
            const circle = document.createElementNS(xmlns, "circle");
            circle.setAttribute("cx", x);
            circle.setAttribute("cy", y);
            circle.setAttribute("r", nodeRadius);
            circle.setAttribute("fill", "#4A6A8F");
            svg.appendChild(circle);

            // Thêm text cho node
            const text = document.createElementNS(xmlns, "text");
            text.setAttribute("x", x);
            text.setAttribute("y", y);
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("dominant-baseline", "middle");
            text.setAttribute("fill", "white");
            text.setAttribute("font-weight", "bold");
            text.textContent = group.name;
            svg.appendChild(text);

            // Thêm text cho mã nhóm
            const codeText = document.createElementNS(xmlns, "text");
            codeText.setAttribute("x", x);
            codeText.setAttribute("y", y + 20);
            codeText.setAttribute("text-anchor", "middle");
            codeText.setAttribute("dominant-baseline", "middle");
            codeText.setAttribute("fill", "white");
            codeText.setAttribute("font-size", "12px");
            codeText.textContent = group.code;
            svg.appendChild(codeText);
        });

        // Tạo marker cho mũi tên
        const defs = document.createElementNS(xmlns, "defs");
        svg.appendChild(defs);

        const marker = document.createElementNS(xmlns, "marker");
        marker.setAttribute("id", "arrowhead");
        marker.setAttribute("markerWidth", "10");
        marker.setAttribute("markerHeight", "7");
        marker.setAttribute("refX", "10");
        marker.setAttribute("refY", "3.5");
        marker.setAttribute("orient", "auto");
        defs.appendChild(marker);

        const polygon = document.createElementNS(xmlns, "polygon");
        polygon.setAttribute("points", "0 0, 10 3.5, 0 7");
        polygon.setAttribute("fill", "#007bff");
        marker.appendChild(polygon);

        // Vẽ các đường nối (tuyến đường)
        routes.forEach(route => {
            const fromPos = nodePositions[route.from_id];
            const toPos = nodePositions[route.to_id];

            if (!fromPos || !toPos) return;

            // Tính toán điểm bắt đầu và kết thúc của đường nối
            const angle = Math.atan2(toPos.y - fromPos.y, toPos.x - fromPos.x);
            const x1 = fromPos.x + (nodeRadius * Math.cos(angle));
            const y1 = fromPos.y + (nodeRadius * Math.sin(angle));
            const x2 = toPos.x - (nodeRadius * Math.cos(angle));
            const y2 = toPos.y - (nodeRadius * Math.sin(angle));

            // Tạo đường nối
            const path = document.createElementNS(xmlns, "path");
            const controlX = (x1 + x2) / 2;
            const controlY = (y1 + y2) / 2 - 50; // Lệch lên trên để tạo đường cong

            path.setAttribute("d", `M${x1},${y1} Q${controlX},${controlY} ${x2},${y2}`);
            path.setAttribute("stroke", route.package_id ? "#28a745" : "#007bff");
            path.setAttribute("stroke-width", "3");
            path.setAttribute("fill", "none");
            path.setAttribute("marker-end", "url(#arrowhead)");
            svg.appendChild(path);

            // Thêm nhãn cho tuyến đường nếu có gói dịch vụ cụ thể
            if (route.package_name && route.package_name !== 'Tất cả') {
                const textPath = document.createElementNS(xmlns, "text");
                textPath.setAttribute("x", controlX);
                textPath.setAttribute("y", controlY - 10);
                textPath.setAttribute("text-anchor", "middle");
                textPath.setAttribute("fill", "#28a745");
                textPath.setAttribute("font-size", "12px");
                textPath.textContent = route.package_name;
                svg.appendChild(textPath);
            }
        });
    }

    // Hàm đọc cookie CSRF token
    function readCookie(name) {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.indexOf(name + '=') === 0) {
                return cookie.substring(name.length + 1, cookie.length);
            }
        }
        return null;
    }
})();