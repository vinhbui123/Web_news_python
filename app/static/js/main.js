(function ($) {
    "use strict";
    
    // Sticky Navbar
    $(window).scroll(function () {
        if ($(this).scrollTop() > 90) {
            $('.header').addClass('header-sticky');
        } else {
            $('.header').removeClass('header-sticky');
        }
    });
    
    
    // Dropdown on mouse hover
    $(document).ready(function () {
        function toggleNavbarMethod() {
            if ($(window).width() > 768) {
                $('.navbar .dropdown').on('mouseover', function () {
                    $('.dropdown-toggle', this).trigger('click');
                }).on('mouseout', function () {
                    $('.dropdown-toggle', this).trigger('click').blur();
                });
            } else {
                $('.navbar .dropdown').off('mouseover').off('mouseout');
            }
        }
        toggleNavbarMethod();
        $(window).resize(toggleNavbarMethod);
    });
    
    
    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 100) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });
    
    
    // Category News Slider
    $('.cn-slider').slick({
        autoplay: false,
        infinite: true,
        dots: false,
        slidesToShow: 2,
        slidesToScroll: 1,
        responsive: [
            {
                breakpoint: 1200,
                settings: {
                    slidesToShow: 2
                }
            },
            {
                breakpoint: 992,
                settings: {
                    slidesToShow: 1
                }
            },
            {
                breakpoint: 768,
                settings: {
                    slidesToShow: 2
                }
            },
            {
                breakpoint: 576,
                settings: {
                    slidesToShow: 1
                }
            }
        ]
    });
})(jQuery);
$(document).ready(function() {
    // 1. Mở Chatbox
    $('#chatBtn').click(function() {
      $('#chatBox').fadeIn();
      $(this).fadeOut(); // Ẩn nút chat khi mở box
    });

    // 2. Đóng Chatbox
    $('#closeChat').click(function() {
      $('#chatBox').fadeOut();
      $('#chatBtn').fadeIn(); // Hiện lại nút chat
    });

    // 3. Xử lý gửi tin nhắn
    function sendMessage() {
      var message = $('#chatInput').val();
      if (message.trim() === '') return;

      // Thêm tin nhắn của người dùng vào giao diện
      var userHtml = `
        <div class="message user-message">
          <p>${message}</p>
          <span class="time">Vừa xong</span>
        </div>`;
      $('#chatBody').append(userHtml);
      $('#chatInput').val(''); // Xóa ô nhập
      
      // Tự động cuộn xuống cuối
      $('#chatBody').scrollTop($('#chatBody')[0].scrollHeight);

      // --- GIẢ LẬP AI TRẢ LỜI (Sau này bạn sẽ thay bằng gọi API Django) ---
      setTimeout(function() {
        var botResponse = "Cảm ơn bạn đã hỏi: '" + message + "'. Hiện tại tôi là bản demo, hãy kết nối tôi với Django Backend để tôi thông minh hơn nhé!";
        
        var botHtml = `
          <div class="message bot-message">
            <p>${botResponse}</p>
            <span class="time">Vừa xong</span>
          </div>`;
          
        $('#chatBody').append(botHtml);
        $('#chatBody').scrollTop($('#chatBody')[0].scrollHeight);
      }, 1000); // Đợi 1 giây giả vờ suy nghĩ
    }

    // Sự kiện click nút Gửi
    $('#sendBtn').click(function() {
      sendMessage();
    });

    // Sự kiện nhấn Enter
    $('#chatInput').keypress(function(e) {
      if (e.which == 13) {
        sendMessage();
      }
    });
  });

  $(document).ready(function() {
    // 1. Mở Chatbox
    $('#chatBtn').click(function() {
      $('#chatBox').fadeIn();
      $(this).fadeOut(); // Ẩn nút chat khi mở box
    });

    // 2. Đóng Chatbox
    $('#closeChat').click(function() {
      $('#chatBox').fadeOut();
      $('#chatBtn').fadeIn(); // Hiện lại nút chat
    });

    // 3. Xử lý gửi tin nhắn
    function sendMessage() {
      var message = $('#chatInput').val();
      if (message.trim() === '') return;

      // Thêm tin nhắn của người dùng vào giao diện
      var userHtml = `
        <div class="message user-message">
          <p>${message}</p>
          <span class="time">Vừa xong</span>
        </div>`;
      $('#chatBody').append(userHtml);
      $('#chatInput').val(''); // Xóa ô nhập
      
      // Tự động cuộn xuống cuối
      $('#chatBody').scrollTop($('#chatBody')[0].scrollHeight);

      // --- GIẢ LẬP AI TRẢ LỜI (Sau này bạn sẽ thay bằng gọi API Django) ---
      setTimeout(function() {
        var botResponse = "Cảm ơn bạn đã hỏi: '" + message + "'. Hiện tại tôi là bản demo, hãy kết nối tôi với Django Backend để tôi thông minh hơn nhé!";
        
        var botHtml = `
          <div class="message bot-message">
            <p>${botResponse}</p>
            <span class="time">Vừa xong</span>
          </div>`;
          
        $('#chatBody').append(botHtml);
        $('#chatBody').scrollTop($('#chatBody')[0].scrollHeight);
      }, 1000); // Đợi 1 giây giả vờ suy nghĩ
    }

    // Sự kiện click nút Gửi
    $('#sendBtn').click(function() {
      sendMessage();
    });

    // Sự kiện nhấn Enter
    $('#chatInput').keypress(function(e) {
      if (e.which == 13) {
        sendMessage();
      }
    });
  });
