/**
 * Shriji Travels — Django Frontend Interactive JavaScript
 */
(function() {
  "use strict";

  /* ==========================================================================
     1. THEME SWITCHER (DARK / LIGHT MODE)
     ========================================================================== */
  var themeToggleBtn = document.getElementById("themeToggleBtn");
  if (themeToggleBtn) {
    var savedTheme = localStorage.getItem("shriji_theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);

    themeToggleBtn.addEventListener("click", function() {
      var current = document.documentElement.getAttribute("data-theme");
      var next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("shriji_theme", next);
    });
  }

  /* ==========================================================================
     2. HOME SEARCH ENGINE HELPERS (SWAP & DATES)
     ========================================================================== */
  var swapBtn = document.getElementById("swapBtn");
  if (swapBtn) {
    swapBtn.addEventListener("click", function() {
      var fromSel = document.getElementById("fromCity");
      var toSel = document.getElementById("toCity");
      if (fromSel && toSel) {
        var tmp = fromSel.value;
        fromSel.value = toSel.value;
        toSel.value = tmp;
      }
    });
  }

  var travelDateInput = document.getElementById("travelDate");
  var chipToday = document.getElementById("chipToday");
  var chipTomorrow = document.getElementById("chipTomorrow");
  var chipDayAfter = document.getElementById("chipDayAfter");

  function setDateOffset(days) {
    var d = new Date();
    d.setDate(d.getDate() + days);
    var dateStr = d.toISOString().slice(0, 10);
    if (travelDateInput) travelDateInput.value = dateStr;
    document.querySelectorAll(".date-chip").forEach(function(c) { c.classList.remove("active"); });
  }

  if (chipToday) chipToday.addEventListener("click", function() { setDateOffset(0); chipToday.classList.add("active"); });
  if (chipTomorrow) chipTomorrow.addEventListener("click", function() { setDateOffset(1); chipTomorrow.classList.add("active"); });
  if (chipDayAfter) chipDayAfter.addEventListener("click", function() { setDateOffset(2); chipDayAfter.classList.add("active"); });

  /* ==========================================================================
     3. INTERACTIVE SEAT SELECTION & COACH FLOOR PLAN
     ========================================================================== */
  var selectedSeats = [];
  var currentDeck = "lower";
  var appliedDiscount = 0;
  var appliedCode = "";

  function initSeatSelection() {
    var seatGrid = document.getElementById("seatGrid");
    if (!seatGrid || !window.BUS_CONFIG) return;

    var bookedSeatsEl = document.getElementById("booked-seats-data");
    var bookedSeats = bookedSeatsEl ? JSON.parse(bookedSeatsEl.textContent) : [];

    renderSeatGrid(bookedSeats);

    // Deck switcher
    var tabLower = document.getElementById("tabLowerDeck");
    var tabUpper = document.getElementById("tabUpperDeck");

    if (tabLower && tabUpper) {
      tabLower.addEventListener("click", function() {
        currentDeck = "lower";
        tabLower.classList.add("btn-navy", "active");
        tabLower.classList.remove("btn-outline-navy");
        tabUpper.classList.add("btn-outline-navy");
        tabUpper.classList.remove("btn-navy", "active");
        renderSeatGrid(bookedSeats);
      });

      tabUpper.addEventListener("click", function() {
        currentDeck = "upper";
        tabUpper.classList.add("btn-navy", "active");
        tabUpper.classList.remove("btn-outline-navy");
        tabLower.classList.add("btn-outline-navy");
        tabLower.classList.remove("btn-navy", "active");
        renderSeatGrid(bookedSeats);
      });
    }

    // Coupon Apply Button
    var applyCouponBtn = document.getElementById("applyCouponBtn");
    var couponInput = document.getElementById("couponInput");
    var couponMsg = document.getElementById("couponMsg");

    if (applyCouponBtn && couponInput) {
      applyCouponBtn.addEventListener("click", function() {
        var code = couponInput.value.trim().toUpperCase();
        if (!code) return;

        var baseFare = window.BUS_CONFIG.fare * selectedSeats.length;
        fetch("/api/validate-coupon/?code=" + encodeURIComponent(code) + "&fare=" + baseFare)
          .then(function(res) { return res.json(); })
          .then(function(data) {
            if (data.valid) {
              appliedDiscount = data.discount;
              appliedCode = data.code;
              couponMsg.className = "small fw-bold mt-1 text-success";
              couponMsg.textContent = data.message;
            } else {
              appliedDiscount = 0;
              appliedCode = "";
              couponMsg.className = "small fw-bold mt-1 text-danger";
              couponMsg.textContent = data.message;
            }
            updateFareSummary();
          })
          .catch(function() {});
      });
    }
  }

  function renderSeatGrid(bookedSeats) {
    var seatGrid = document.getElementById("seatGrid");
    if (!seatGrid) return;
    seatGrid.innerHTML = "";

    var isSleeper = window.BUS_CONFIG.isSleeper;
    var rows = isSleeper ? 5 : Math.ceil(window.BUS_CONFIG.totalSeats / 4);

    for (var r = 1; r <= rows; r++) {
      var rowEl = document.createElement("div");
      rowEl.className = "seat-row";

      if (isSleeper) {
        var prefix = currentDeck === "lower" ? "L" : "U";
        var s1 = prefix + (r * 3 - 2);
        var s2 = prefix + (r * 3 - 1);
        var s3 = prefix + (r * 3);

        var leftPair = document.createElement("div");
        leftPair.className = "seat-pair";
        leftPair.appendChild(createSeatBtn(s1, bookedSeats, true));
        leftPair.appendChild(createSeatBtn(s2, bookedSeats, true));
        rowEl.appendChild(leftPair);

        var aisle = document.createElement("div");
        aisle.className = "seat-aisle-gap";
        rowEl.appendChild(aisle);

        var rightPair = document.createElement("div");
        rightPair.className = "seat-pair";
        rightPair.appendChild(createSeatBtn(s3, bookedSeats, true));
        rowEl.appendChild(rightPair);
      } else {
        var leftPair2 = document.createElement("div");
        leftPair2.className = "seat-pair";
        leftPair2.appendChild(createSeatBtn("A" + r, bookedSeats, false));
        leftPair2.appendChild(createSeatBtn("B" + r, bookedSeats, false));
        rowEl.appendChild(leftPair2);

        var aisle2 = document.createElement("div");
        aisle2.className = "seat-aisle-gap";
        rowEl.appendChild(aisle2);

        var rightPair2 = document.createElement("div");
        rightPair2.className = "seat-pair";
        rightPair2.appendChild(createSeatBtn("C" + r, bookedSeats, false));
        rightPair2.appendChild(createSeatBtn("D" + r, bookedSeats, false));
        rowEl.appendChild(rightPair2);
      }

      seatGrid.appendChild(rowEl);
    }
  }

  function createSeatBtn(code, bookedSeats, isSleeper) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "seat-btn" + (isSleeper ? " sleeper" : "");
    btn.textContent = code;

    if (bookedSeats.indexOf(code) !== -1) {
      btn.classList.add("booked");
      btn.disabled = true;
    } else {
      if (selectedSeats.indexOf(code) !== -1) {
        btn.classList.add("selected");
      }
      btn.addEventListener("click", function() {
        var idx = selectedSeats.indexOf(code);
        if (idx === -1) {
          if (selectedSeats.length >= 6) {
            alert("Maximum 6 seats allowed per reservation.");
            return;
          }
          selectedSeats.push(code);
          btn.classList.add("selected");
        } else {
          selectedSeats.splice(idx, 1);
          btn.classList.remove("selected");
        }
        updateFareSummary();
        renderDynamicPassengerRows();
      });
    }

    return btn;
  }

  function updateFareSummary() {
    var count = selectedSeats.length;
    var baseFare = count * (window.BUS_CONFIG ? window.BUS_CONFIG.fare : 0);
    var gst = Math.round((baseFare - appliedDiscount) * 0.05);
    var total = Math.max(0, baseFare - appliedDiscount + gst);

    var selSeatsInput = document.getElementById("selectedSeatsInput");
    if (selSeatsInput) selSeatsInput.value = selectedSeats.join(",");

    var selSeatCount = document.getElementById("selSeatCount");
    if (selSeatCount) selSeatCount.textContent = count;

    var selSeatsText = document.getElementById("selSeatsText");
    if (selSeatsText) selSeatsText.textContent = count > 0 ? selectedSeats.sort().join(", ") : "—";

    var baseFareText = document.getElementById("baseFareText");
    if (baseFareText) baseFareText.textContent = "₹" + baseFare.toLocaleString("en-IN");

    var discountRow = document.getElementById("discountRow");
    if (discountRow) {
      if (appliedDiscount > 0) {
        discountRow.style.display = "flex";
        document.getElementById("appliedCodeText").textContent = appliedCode;
        document.getElementById("discountAmountText").textContent = "-₹" + appliedDiscount.toLocaleString("en-IN");
      } else {
        discountRow.style.display = "none";
      }
    }

    var gstAmountText = document.getElementById("gstAmountText");
    if (gstAmountText) gstAmountText.textContent = "₹" + gst.toLocaleString("en-IN");

    var totalAmountText = document.getElementById("totalAmountText");
    if (totalAmountText) totalAmountText.textContent = "₹" + total.toLocaleString("en-IN");

    var proceedBtn = document.getElementById("proceedBtn");
    if (proceedBtn) proceedBtn.disabled = count === 0;
  }

  function renderDynamicPassengerRows() {
    var container = document.getElementById("dynamicPassengersContainer");
    if (!container) return;
    container.innerHTML = "";

    selectedSeats.forEach(function(seat, idx) {
      var row = document.createElement("div");
      row.className = "p-2 bg-light rounded-3 mb-2 border";
      row.innerHTML = '' +
        '<div class="d-flex justify-content-between small fw-bold text-navy mb-1">' +
          '<span>Passenger ' + (idx + 1) + ' (Seat: <strong>' + seat + '</strong>)</span>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' +
            '<input type="text" name="pass_name_' + idx + '" class="form-control form-control-sm" placeholder="Full Name" value="' + (idx === 0 && document.getElementById("leadName") ? document.getElementById("leadName").value : "") + '" required>' +
          '</div>' +
          '<div class="col-3">' +
            '<input type="number" name="pass_age_' + idx + '" class="form-control form-control-sm" placeholder="Age" min="1" max="100" value="28" required>' +
          '</div>' +
          '<div class="col-3">' +
            '<select name="pass_gender_' + idx + '" class="form-select form-select-sm">' +
              '<option value="Male">Male</option>' +
              '<option value="Female">Female</option>' +
              '<option value="Other">Other</option>' +
            '</select>' +
          '</div>' +
        '</div>';
      container.appendChild(row);
    });
  }

  /* ==========================================================================
     4. CREDIT CARD LIVE FORMATTING & PREVIEW
     ========================================================================== */
  var cardNumInput = document.getElementById("cardNumInput");
  var cardExpInput = document.getElementById("cardExpInput");
  var cardHolderInput = document.getElementById("cardHolderInput");

  if (cardNumInput) {
    cardNumInput.addEventListener("input", function() {
      var v = cardNumInput.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
      var formatted = "";
      for (var i = 0; i < v.length; i++) {
        if (i > 0 && i % 4 === 0) formatted += " ";
        formatted += v[i];
      }
      cardNumInput.value = formatted;
      var d = document.getElementById("cardNumDisplay");
      if (d) d.textContent = formatted || "4532 •••• •••• 5678";
    });
  }

  if (cardExpInput) {
    cardExpInput.addEventListener("input", function() {
      var d = document.getElementById("cardExpDisplay");
      if (d) d.textContent = cardExpInput.value || "12/28";
    });
  }

  if (cardHolderInput) {
    cardHolderInput.addEventListener("input", function() {
      var d = document.getElementById("cardHolderDisplay");
      if (d) d.textContent = cardHolderInput.value.toUpperCase() || "VALUED TRAVELER";
    });
  }

  /* ==========================================================================
     5. BARCODE & QR CODE GENERATORS (SVG)
     ========================================================================== */
  window.generateBarcodeSVG = function(code) {
    var str = String(code || "").toUpperCase();
    var bars = [];
    var x = 6;
    bars.push('<rect x="' + x + '" y="0" width="2.5" height="46" fill="#0A192F" />');
    x += 4.5;
    bars.push('<rect x="' + x + '" y="0" width="1.5" height="46" fill="#0A192F" />');
    x += 3.5;

    for (var j = 0; j < str.length; j++) {
      var c = str.charCodeAt(j);
      var w1 = ((c % 3) * 0.9 + 1.2).toFixed(1);
      var s1 = (((c >> 1) % 3) * 0.8 + 1.6).toFixed(1);
      var w2 = (((c >> 2) % 3) * 0.9 + 1.4).toFixed(1);
      var s2 = (((c >> 3) % 2) * 0.8 + 1.8).toFixed(1);

      bars.push('<rect x="' + x.toFixed(1) + '" y="0" width="' + w1 + '" height="46" fill="#0A192F" />');
      x += parseFloat(w1) + parseFloat(s1);
      bars.push('<rect x="' + x.toFixed(1) + '" y="0" width="' + w2 + '" height="46" fill="#0A192F" />');
      x += parseFloat(w2) + parseFloat(s2);
    }

    bars.push('<rect x="' + x.toFixed(1) + '" y="0" width="1.5" height="46" fill="#0A192F" />');
    x += 3.5;
    bars.push('<rect x="' + x.toFixed(1) + '" y="0" width="2.5" height="46" fill="#0A192F" />');
    x += 6;

    return '<svg viewBox="0 0 ' + Math.ceil(x) + ' 46" width="100%" height="46" preserveAspectRatio="none">' + bars.join('') + '</svg>';
  };

  window.generateQRCodeSVG = function(text) {
    var size = 25;
    var rects = [];
    var hash = 0;
    for (var i = 0; i < text.length; i++) {
      hash = ((hash << 5) - hash) + text.charCodeAt(i);
      hash |= 0;
    }

    function drawCorner(startX, startY) {
      rects.push('<rect x="' + startX + '" y="' + startY + '" width="7" height="7" fill="#0A192F"/>');
      rects.push('<rect x="' + (startX + 1) + '" y="' + (startY + 1) + '" width="5" height="5" fill="#FFFFFF"/>');
      rects.push('<rect x="' + (startX + 2) + '" y="' + (startY + 2) + '" width="3" height="3" fill="#0A192F"/>');
    }

    drawCorner(1, 1);
    drawCorner(size - 8, 1);
    drawCorner(1, size - 8);

    for (var r = 0; r < size; r++) {
      for (var c = 0; c < size; c++) {
        if ((r < 8 && c < 8) || (r < 8 && c >= size - 8) || (r >= size - 8 && c < 8)) continue;
        var val = Math.abs(Math.sin((r * size + c) * 0.4 + hash));
        if (val > 0.5) {
          rects.push('<rect x="' + c + '" y="' + r + '" width="1" height="1" fill="#0A192F"/>');
        }
      }
    }

    return '<svg viewBox="0 0 ' + size + ' ' + size + '" width="120" height="120">' +
      '<rect width="' + size + '" height="' + size + '" fill="#FFFFFF"/>' +
      rects.join('') +
    '</svg>';
  };

  /* ==========================================================================
     6. CHATBOT INTERACTIONS & GLOBAL HELPERS
     ========================================================================== */
  var chatTriggerBtn = document.getElementById("chatTriggerBtn");
  var chatWindow = document.getElementById("chatWindow");
  var chatCloseBtn = document.getElementById("chatCloseBtn");
  var chatForm = document.getElementById("chatForm");
  var chatInput = document.getElementById("chatInput");
  var chatMessages = document.getElementById("chatMessages");

  if (chatTriggerBtn && chatWindow) {
    chatTriggerBtn.addEventListener("click", function() {
      chatWindow.style.display = chatWindow.style.display === "none" ? "flex" : "none";
    });
  }

  if (chatCloseBtn && chatWindow) {
    chatCloseBtn.addEventListener("click", function() {
      chatWindow.style.display = "none";
    });
  }

  if (chatForm && chatInput) {
    chatForm.addEventListener("submit", function(e) {
      e.preventDefault();
      var q = chatInput.value.trim();
      if (!q) return;
      appendChatMsg("user", q);
      chatInput.value = "";

      setTimeout(function() {
        processChatResponse(q);
      }, 500);
    });
  }

  function appendChatMsg(sender, text) {
    if (!chatMessages) return;
    var el = document.createElement("div");
    el.className = "chat-msg " + sender + (sender === "user" ? " text-end text-primary fw-bold" : "");
    el.innerHTML = '<p class="mb-0">' + text + '</p>';
    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function processChatResponse(q) {
    var lower = q.toLowerCase();
    var rep = "I can help with checking PNR status, finding buses, baggage rules, and discounts. What would you like to know?";

    if (lower.includes("pnr") || lower.includes("track")) {
      rep = "You can check your PNR status or live radar telemetry in the 'My Tickets' or 'Live GPS Radar' tabs!";
    } else if (lower.includes("coupon") || lower.includes("offer")) {
      rep = "🎉 Use coupon SHRIJI20 for 20% OFF on all Sleeper Coaches, or FIRST50 for flat ₹50 OFF!";
    } else if (lower.includes("refund") || lower.includes("cancel")) {
      rep = "Cancellations made 12+ hours prior receive a 90% instant refund processed back to your original payment method.";
    }

    appendChatMsg("bot", rep);
  }

  window.askBot = function(topic) {
    if (chatInput) chatInput.value = topic;
    if (chatForm) chatForm.dispatchEvent(new Event("submit"));
  };

  window.copyCode = function(code) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(code);
    }
    alert("Copied Promo Code: " + code);
  };

  // Run on DOM Ready
  document.addEventListener("DOMContentLoaded", function() {
    initSeatSelection();
  });

})();
