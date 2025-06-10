// 查詢 API 並將結果渲染到表格
function search() {
  const dateInput = document.getElementById("dateInput").value;
  const branchSelect = document.getElementById("branchSelect").value;

  let url = "";
  const queryParams = [];

  if (dateInput) queryParams.push(`date=${dateInput}`);
  if (branchSelect === "無") {
    url = "/api/inbounds";
  } else {
    url = "/api/branch_incomplete";
    queryParams.push(`branch=${encodeURIComponent(branchSelect)}`);
  }

  const queryString = queryParams.length > 0 ? `?${queryParams.join("&")}` : "";

  fetch(`${url}${queryString}`)
    .then(response => response.json())
    .then(data => {
      const feedback = document.getElementById("feedback");
      const tableContainer = document.getElementById("tableContainer");
      tableContainer.innerHTML = ""; // ⛔ 先清空原本表格，避免重複新增

      if (data.length === 0) {
        feedback.innerText = `⚠️ 分公司: ${branchSelect}， ${dateInput}，查無資料。`;
        feedback.style.color = "orange";
        return;
      }

      feedback.innerText = `✅ 分公司: ${branchSelect}， ${dateInput}，共 ${data.length} 筆資料。`;
      feedback.style.color = "green";

      // 取得 inputdate 欄位的最新時間（含時分秒）
      const latestInputDate = data.reduce((latest, item) => {
        if (!item.inputdate) return latest;

        // 將字串轉為 Date 物件（處理 Safari 的日期格式問題）
        const current = new Date(item.inputdate.replace(/-/g, '/'));

        return current > latest ? current : latest;
      }, new Date(0)); // 初始值為 1970-01-01 00:00:00

      // 直接用 Date 物件顯示，會顯示本地時間（含 GMT+0800）
      console.log("📅 最新 inputdate：", latestInputDate);

      // 🧱 動態建立 table HTML 結構
      const table = document.createElement("table");
      table.id = "caseTable";
      table.className = "display";

      const thead = document.createElement("thead");
      thead.innerHTML = branchSelect === "無" ? `
        <tr>
          <th>序號</th>
          <th>選取</th>
          <th>登錄日期</th>
          <th>案件編號</th>
          <th>客戶名稱</th>
          <th>手機號碼</th>
          <th>指派營業員</th>
          <th>信件狀態</th>
        </tr>
      ` : `
        <tr>
          <th>序號</th>
          <th>選取</th>
          <th>登錄日期</th>
          <th>案件編號</th>
          <th>客戶名稱</th>
          <th>手機號碼</th>
          <th>營業員</th>
          <th>通知補件時間</th>
          <th>狀態</th>
          <th>信件狀態</th>
        </tr>
      `;

      const tbody = document.createElement("tbody");
      const today = new Date();

      data.forEach((item, index) => {
        const tr = document.createElement("tr");

        // 日期標示
        let dateClass = 'date-warm-normal';
        if (item.register_date) {
          const regDate = new Date(item.register_date.replace(/-/g, '/'));
          const diffDays = Math.floor((today - regDate) / (1000 * 60 * 60 * 24));
          if (diffDays <= 5) dateClass = 'date-warm-good';
          else if (diffDays <= 10) dateClass = 'date-warm-warning';
          else if (diffDays <= 30) dateClass = 'date-warm-alert';
          else dateClass = 'date-warm-dead';
        }

      // 狀態圖示
      const redStatuses = ["等待客戶補件", "未提醒", "客戶填寫未完成"];
      const greenStatuses = ["經辦作業 or AE KYC處理中", "已回覆"];
      const yellowStatuses = ["待回覆"];
      let statusClass = "", statusIcon = "",mail_status_Class = "",mail_status_Icon = "";

      if (redStatuses.includes(item.mail_status)) {
        mail_status_Class = 'status-red'; mail_status_Icon = '🔴';
      } else if (greenStatuses.includes(item.mail_status)) {
        mail_status_Class = 'status-green'; mail_status_Icon = '🟢';
      } else if (yellowStatuses.includes(item.mail_status)) {
        mail_status_Class = 'status-yellow'; mail_status_Icon = '🟡';
      }

      if (redStatuses.includes(item.status)) {
        statusClass = 'status-red'; statusIcon = '🔴';
      } else if (greenStatuses.includes(item.status)) {
        statusClass = 'status-green'; statusIcon = '🟢';
      } else if (yellowStatuses.includes(item.status)) {
        statusClass = 'status-yellow'; statusIcon = '🟡';
      }

      const displayStatus = item.mail_status === "待回覆"
        ? "等待 AE 回覆"
        : item.mail_status === "未提醒"
          ? "尚未通知 AE"
          : (item.mail_status || "");

      const searchButton = item.mail_status
        ? `<button class="status-icon-search" title="搜尋此狀態">🔍</button>`
        : "";

      const statusHTML = `
      <span class="${statusClass}">
        <span class="status-icon-label">${statusIcon} ${item.status}</span>
      </span>`;

      const mail_statusHTML = `
      <span class="${mail_status_Class}">
        <span class="status-icon-label">${mail_status_Icon} ${displayStatus}</span>
        ${searchButton}
      </span>`;

        // 填入欄位
        tr.innerHTML = branchSelect === "無" ? `
          <td>${index + 1}</td>
          <td><input type="checkbox" name="selectRow" value="${item.case_id}"></td>
          <td class="${dateClass}">${item.register_date || ''}</td>
          <td>${item.case_id}</td>
          <td>${item.customer_name || ''}</td>
          <td>${item.phone || ''}</td>
          <td>${item.assigned_sales || ''}</td>
          <td>${mail_statusHTML}</td>
        ` : `
          <td>${index + 1}</td>
          <td><input type="checkbox" name="selectRow" value="${item.case_id}"></td>
          <td class="${dateClass}">${item.register_date || ''}</td>
          <td>${item.case_id}</td>
          <td>${item.customer_name || ''}</td>
          <td>${item.phone || ''}</td>
          <td>${item.sales || ''}</td>
          <td>${item.last_return_time || ''}</td>
          <td>${statusHTML}</td>
          <td>${mail_statusHTML}</td>
        `;

        tr.addEventListener('click', function (e) {
          if (e.target.tagName.toLowerCase() === 'input') return;
          const checkbox = tr.querySelector('input[type="checkbox"]');
          checkbox.checked = !checkbox.checked;
          tr.classList.toggle('selected', checkbox.checked);
        });

        tbody.appendChild(tr);
      });

      table.appendChild(thead);
      table.appendChild(tbody);
      tableContainer.appendChild(table); // ✅ 放進容器

      // 初始化 DataTable
      $('#caseTable').DataTable({
        language: {
          url: "https://cdn.datatables.net/plug-ins/1.13.6/i18n/zh-HANT.json"
        },
        order: [[2, "desc"]],
        columnDefs: [
          { orderable: false, targets: 1 } // 第二欄選取框不排序
        ]
      });
    })
    .catch(error => {
      const feedback = document.getElementById("feedback");
      console.error("資料載入失敗：", error);
      feedback.innerText = "❌ 查詢失敗，請稍後再試。";
      feedback.style.color = "red";
    });
}

// 自動戴入今天日期
window.addEventListener("DOMContentLoaded", () => {
  const dateInput = document.getElementById("dateInput");
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
  }
  search();
});

// 開啟指派功能
function assignAE() {
  const selectedRows = Array.from(document.querySelectorAll("input[name='selectRow']:checked"))
    .map(cb => {
      const tr = cb.closest('tr');
      return {
        case_id: cb.value,
        record_date: dateInput.value
      };
    });

  if (selectedRows.length === 0) {
    alert("請先選取要指派的案件");
    return;
  }

  if (selectedRows.length > 1) {
    const confirmAssign = confirm("⚠️ 確定要全部指派到同一個 AE?");
    if (!confirmAssign) return;
  }

  window.selectedRecords = selectedRows;
 // 👉 清空選單與輸入欄位
 document.getElementById("deptSelect").value = "";
 document.getElementById("nameSelect").innerHTML = '<option value="">請選擇姓名</option>';
 document.getElementById("idSearchInput").value = "";
 document.getElementById("salesInput").value = "";
 document.getElementById("Recipient").value = "";
 document.getElementById("assignModal").style.display = "block";
 loadOrganizationTable();
}

// 關閉指派視窗
function closeAssignModal() {
  document.getElementById("assignModal").style.display = "none";
}

// 指派AE
function confirmAssign() {
  const Recipient = document.getElementById("nameSelect").value.trim();
  if (!Recipient) {
    alert("請選擇營業員");
    return;
  }

  fetch('/api/inbounds/assign', {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      records: window.selectedRecords,
      sales: Recipient
    })
  })
  .then(res => {
    if (!res.ok) throw new Error("指派失敗");
    return res.json();
  })
  .then(data => {
    alert("✅ 指派成功！");
    closeAssignModal();
    search();

    // ↓↓↓ 新增：指派成功後自動寄送「自來客_指派AE」郵件 ↓↓↓
    const detailedRecords = window.selectedRecords.map(rec => {
      // 利用案件編號去找當前 table 裡對應的 <tr>，並讀出客戶名稱與手機
      const selector = `tr input[value="${rec.case_id}"]`; 
      const tr = document.querySelector(selector)?.closest('tr');
      let customer = "", phone = "";
      if (tr) {
        const tds = tr.querySelectorAll('td');
        customer = tds[4]?.innerText.trim() || "";
        phone    = tds[5]?.innerText.trim() || "";
      }
      return {
        case_id: rec.case_id,
        record_date: rec.record_date,
        customer_name: customer,
        phone: phone
      };
    });
    const recipient = document.getElementById("Recipient").value.trim();
    const subject = "線上開戶未填公司及AE名單";
    const body = "請聯繫客戶確認是否有指定服務營業員，若沒有服務AE則為自來戶請協助客戶完成線上開戶，並回報進度，謝謝。";

    fetch(`/api/send-email?type=${encodeURIComponent('3')}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        recipient, 
        subject, 
        body, 
        records: detailedRecords   // 這裡帶入 customer_name 與 phone
      })
    })
    .then(res2 => {
      if (!res2.ok) throw new Error("自動寄信失敗");
      return res2.json();
    })
    .then(emailData => {
      alert("✅ 已自動寄送「自來客_指派AE」郵件");
      search();  // 若要更新列表
    })
    .catch(err2 => {
      console.error("自動寄信錯誤：", err2);
      alert("❌ 自動寄送「自來客_指派AE」信件失敗：" + err2.message);
    });
  })
  .catch(err => {
    alert("❌ 指派失敗：" + err.message);
  });
}

// 載入組織圖
let orgData = [];
function loadOrganizationTable() {
  fetch('/api/organization')
    .then(res => res.json())
    .then(data => {
      orgData = data;

      // ----- 更新 assignModal 的組織資料（原本的 id 名稱） -----
      const assignDeptSelect = document.getElementById("deptSelect");
      const assignNameSelect = document.getElementById("nameSelect");
      const assignIdSearch = document.getElementById("idSearchInput");
      const Recipient = document.getElementById("Recipient");
      if (assignDeptSelect && assignNameSelect && assignIdSearch) {
        // 填充部門選單
        assignDeptSelect.innerHTML = '<option value="">請選擇部門</option>';
        const deptSet = new Set(data.map(d => d.dept_name));
        deptSet.forEach(dept => {
          const opt = document.createElement("option");
          opt.value = dept;
          opt.textContent = dept;
          assignDeptSelect.appendChild(opt);
        });
        
        // 當部門改變時，更新姓名選單
        assignDeptSelect.onchange = function() {
          assignNameSelect.innerHTML = '<option value="">請選擇姓名</option>';
          orgData.filter(item => item.dept_name === assignDeptSelect.value)
            .forEach(item => {
              const opt = document.createElement("option");
              opt.value = item.name;
              opt.textContent = `${item.name}（${item.employee_id}）`;
              assignNameSelect.appendChild(opt);
            });
        };

        // 當姓名選擇變動時，自動填入隱藏欄位 salesInput
        assignNameSelect.onchange = function(e) {
          const selectedName = e.target.value;
          const found = orgData.find(item => item.name === selectedName);
          if (found) {
            document.getElementById("salesInput").value = found.name;
          }
        };
        // 當姓名改變時，自動更新收件者 Email 欄位
        assignNameSelect.onchange = function(e) {
          const selectedName = e.target.value;
          const found = orgData.find(item => item.name === selectedName);
          if (found && Recipient) {
            Recipient.value = found.email || '';
          }
        };
        // 快速查找：根據輸入的員工編號查詢，並自動更新對應欄位
        assignIdSearch.addEventListener('keydown', function(e) {
          if (e.key === "Enter") {
            const searchId = assignIdSearch.value.trim();
            const found = orgData.find(item => item.employee_id === searchId);
            if (found) {
              assignDeptSelect.value = found.dept_name;
              assignDeptSelect.dispatchEvent(new Event("change"));
              setTimeout(() => {
                assignNameSelect.value = found.name;
                document.getElementById("salesInput").value = found.name;
                if (Recipient) {
                  Recipient.value = found.email || '';
                }
              }, 100);
            } else {
              alert("查無此員鯿！");
            }
          }
        });        
      }

      // ----- 更新 mailsendModal 的組織資料（專屬的 id） -----
      const emailDeptSelect = document.getElementById("emailDeptSelect");
      const emailNameSelect = document.getElementById("emailNameSelect");
      const emailIdSearchInput = document.getElementById("emailIdSearchInput");
      const emailRecipient = document.getElementById("emailRecipient");
      if (emailDeptSelect && emailNameSelect && emailIdSearchInput) {
        // 填充部門選單
        emailDeptSelect.innerHTML = '<option value="">請選擇部門</option>';
        const deptSet2 = new Set(data.map(d => d.dept_name));
        deptSet2.forEach(dept => {
          const opt = document.createElement("option");
          opt.value = dept;
          opt.textContent = dept;
          emailDeptSelect.appendChild(opt);
        });
        
        // 當部門改變時，更新姓名選單
        emailDeptSelect.onchange = function() {
          emailNameSelect.innerHTML = '<option value="">請選擇姓名</option>';
          orgData.filter(item => item.dept_name === emailDeptSelect.value)
            .forEach(item => {
              const opt = document.createElement("option");
              opt.value = item.name;
              opt.textContent = `${item.name}（${item.employee_id}）`;
              emailNameSelect.appendChild(opt);
            });
        };

        // 當姓名改變時，自動更新收件者 Email 欄位
        emailNameSelect.onchange = function(e) {
          const selectedName = e.target.value;
          const found = orgData.find(item => item.name === selectedName);
          if (found && emailRecipient) {
            emailRecipient.value = found.email || '';
          }
        };

        // 快速查找：根據輸入的員工編號查詢，並自動更新對應欄位
        emailIdSearchInput.addEventListener('keydown', function(e) {
          if (e.key === "Enter") {
            const searchId = emailIdSearchInput.value.trim();
            const found = orgData.find(item => item.employee_id === searchId);
            if (found) {
              emailDeptSelect.value = found.dept_name;
              emailDeptSelect.dispatchEvent(new Event("change"));
              setTimeout(() => {
                emailNameSelect.value = found.name;
                if (emailRecipient) {
                  emailRecipient.value = found.email || '';
                }
              }, 100);
            } else {
              alert("查無此員鯿！");
            }
          }
        });        
      }
    });
}

function sendEmail() {
  const selectedRows = Array.from(document.querySelectorAll("input[name='selectRow']:checked"))
    .map(cb => {
      const tr = cb.closest('tr');
      const tds = tr.querySelectorAll("td");
      return {
        case_id: cb.value,
        record_date: dateInput.value,
        customer_name: tds[4]?.innerText.trim() || "",
        phone: tds[5]?.innerText.trim() || ""
      };
    });

  if (selectedRows.length === 0) {
    alert("請先選取要寄送的案件");
    return;
  }

  if (selectedRows.length > 1) {
    const confirmAssign = confirm("⚠️ 確定要寄送多筆信件?");
    if (!confirmAssign) return;
  }

  window.selectedRecords = selectedRows;
  document.getElementById("mailsendModal").style.display = "block";

  // 👇 清空欄位值
  document.getElementById("emailIdSearchInput").value = "";
  document.getElementById("emailDeptSelect").value = "";
  document.getElementById("emailNameSelect").innerHTML = '<option value="">請選擇姓名</option>';
  document.getElementById("emailRecipient").value = "";
  document.getElementById("emailSubject").value = "";
  document.getElementById("emailBody").value = "";
  document.getElementById("emailTypeSelect").value = "";
  loadOrganizationTable();
}

function closeEmailModal() {
  document.getElementById("mailsendModal").style.display = "none";
}

function confirmSendEmail() {
  const recipient = document.getElementById("emailRecipient").value.trim();
  const subject = document.getElementById("emailSubject").value.trim();
  const body = document.getElementById("emailBody").value.trim();
  const selectedType = document.getElementById("emailTypeSelect").value;


  if (!recipient || !subject || !body) {
    alert("請完整填寫信件資訊");
    return;
  }

  fetch(`/api/send-email?type=${encodeURIComponent(selectedType)}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ recipient, subject, body, records: window.selectedRecords})
  })
  .then(res => res.json())
  .then(data => {
    alert("✅ 寄信結果：" + data.message);
    closeEmailModal();
    search();
  })
  .catch(err => {
    alert("❌ 寄信失敗：" + err.message);
  });
}

// 根據選擇的類型，自動載入信件主旨與內文
document.getElementById("emailTypeSelect").addEventListener("change", function () {
  const selectedType = this.value;
  const subjectInput = document.getElementById("emailSubject");
  const bodyTextarea = document.getElementById("emailBody");

  // 清空欄位
  subjectInput.value = "";
  bodyTextarea.value = "";

  if (!selectedType) return; // 若沒選擇，則不處理

  fetch(`/api/EmailContent?type=${selectedType}`)
    .then(res => {
      if (!res.ok) throw new Error("載入信件內容失敗");
      return res.json();
    })
    .then(data => {
      if (Array.isArray(data) && data.length > 0) {
        subjectInput.value = data[0].subject || '';
        bodyTextarea.value = data[0].content || '';
      } else {
        alert("⚠️ 查無對應的信件範本");
      }
    })
    .catch(err => {
      console.error("取得信件內容錯誤：", err);
      alert("❌ 無法載入信件內容，請稍後再試。");
    });
});

// 顯示回覆紀錄的彈跳視窗
document.addEventListener("click", function (event) {
  if (event.target.classList.contains("status-icon-search")) {
    const row = event.target.closest("tr");
    const caseId = row.querySelector("input[type='checkbox']")?.value;
    if (!caseId) {
      alert("⚠️ 無法取得案件編號");
      return;
    }

    fetch(`/api/get_mail_tracking?case_id=${encodeURIComponent(caseId)}`)
      .then(res => res.json())
      .then(data => {
        const container = document.getElementById("mailTrackingTableContainer");
        const modal = document.getElementById("mailTrackingModal");
        const formatDate = dateStr => dateStr?.split('T')[0] || '-';
        const formatTime = dateStr => dateStr?.split('T')[1] || '-';
        if (!Array.isArray(data) || data.length === 0) {
          container.innerHTML = `<p>📭 此案件無回覆紀錄</p>`;
        } else {
          let tableHTML = `
          <table style="
              width: 100%;
              table-layout: auto;
              border-collapse: collapse;
              word-break: break-word;
            " border="1" cellpadding="6" cellspacing="0">
            <thead>
              <tr>
                <th style="width: 120px;">寄件日期</th>
                <th style="width: 80px;">AE</th>
                <th style="width: 80px;">信件類型</th>
                <th style="width: 120px;">回覆日期</th>
                <th style="max-width: 300px;">回覆內容</th>
              </tr>
            </thead>
            <tbody>
        `;
        
        data.forEach(item => {
          tableHTML += `
            <tr>
              <td style="white-space: nowrap;">
                ${formatDate(item.send_date)}<br>${formatTime(item.send_date)}
              </td>
              <td style="white-space: nowrap;">${item.AE || '-'}</td>
              <td style="white-space: nowrap;">${item.mail_type || '-'}</td>
              <td style="white-space: nowrap;">
                ${formatDate(item.response_date)}<br>${formatTime(item.response_date)}
              </td>
              <td style="white-space: normal; word-break: break-word;">${item.response_ans || '-'}</td>
            </tr>`;
        });
        
        tableHTML += `</tbody></table>`;
          container.innerHTML = tableHTML;
        }

        modal.style.display = "block";
      })
      .catch(err => {
        console.error("取得回覆紀錄失敗：", err);
        alert("❌ 查詢回覆紀錄失敗，請稍後再試");
      });
  }
});

// 關閉信件會覆彈跳視窗
function closeMailTrackingModal() {
  const modal = document.getElementById("mailTrackingModal");
  modal.style.display = "none";
}

// 按下 Esc 鍵關閉所有開啟中的 modal
document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    const modals = [
      { id: "mailTrackingModal", closeFn: closeMailTrackingModal },
      { id: "assignModal", closeFn: closeAssignModal },
      { id: "mailsendModal", closeFn: closeEmailModal }
    ];

    modals.forEach(modal => {
      const el = document.getElementById(modal.id);
      if (el && el.style.display === "block") {
        modal.closeFn();
      }
    });
  }
});
