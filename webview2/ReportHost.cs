using System;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;

internal static class ReportHost
{
    private const string Page = "https://sizing.local/index.html";
    private static readonly StreamWriter Output =
        new StreamWriter(Console.OpenStandardOutput(), new UTF8Encoding(false)) { AutoFlush = true };

    [StructLayout(LayoutKind.Sequential)]
    private struct Rect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")]
    private static extern bool GetClientRect(IntPtr hwnd, out Rect rect);
    [DllImport("user32.dll")]
    private static extern short GetKeyState(int key);

    [STAThread]
    private static void Main(string[] args)
    {
        if (args.Length != 3) return;
        // Tk and the host must use the same DPI coordinate space. A DPI-aware
        // host inside the DPI-unaware Tk frame applies Windows scaling twice.
        var parent = new IntPtr(long.Parse(args[0]));
        using (var dispatch = new Control())
        using (var context = new ApplicationContext())
        {
            var handle = dispatch.Handle;
            CoreWebView2Controller controller = null;
            Action resize = () =>
            {
                Rect rect;
                if (controller != null && GetClientRect(parent, out rect))
                {
                    controller.Bounds = Rectangle.FromLTRB(rect.Left, rect.Top, rect.Right, rect.Bottom);
                    controller.NotifyParentWindowPositionChanged();
                }
            };
            var reader = new Thread(() =>
            {
                using (var input = new StreamReader(Console.OpenStandardInput(), Encoding.UTF8))
                {
                    string line;
                    while ((line = input.ReadLine()) != null)
                    {
                        var command = line;
                        try
                        {
                            dispatch.BeginInvoke((Action)(() =>
                            {
                                if (command == "resize") resize();
                                else if (controller != null)
                                    controller.CoreWebView2.PostWebMessageAsJson(command);
                            }));
                        }
                        catch (InvalidOperationException) { return; }
                    }
                }
                try { dispatch.BeginInvoke((Action)(() => context.ExitThread())); }
                catch (InvalidOperationException) { }
            });
            reader.IsBackground = true;
            reader.Start();

            dispatch.BeginInvoke((Action)(async () =>
            {
                try
                {
                    var environment = await CoreWebView2Environment.CreateAsync(null, args[2]);
                    controller = await environment.CreateCoreWebView2ControllerAsync(parent);
                    resize();
                    controller.IsVisible = true;
                    var web = controller.CoreWebView2;
                    web.Settings.AreDevToolsEnabled = false;
                    web.Settings.AreBrowserAcceleratorKeysEnabled = false;
                    web.NavigationStarting += (sender, e) => e.Cancel = e.Uri != Page;
                    web.NewWindowRequested += (sender, e) => e.Handled = true;
                    web.WebMessageReceived += (sender, e) =>
                    {
                        if (e.Source == Page) Output.WriteLine(e.WebMessageAsJson);
                    };
                    controller.AcceleratorKeyPressed += (sender, e) =>
                    {
                        if (e.KeyEventKind != CoreWebView2KeyEventKind.KeyDown) return;
                        bool ctrl = GetKeyState(0x11) < 0;
                        if (e.VirtualKey == 0x74 || (ctrl && e.VirtualKey == 0x0D))
                        {
                            e.Handled = true;
                            Output.WriteLine("{\"event\":\"solve\"}");
                        }
                        else if (ctrl && e.VirtualKey == 0x53)
                        {
                            e.Handled = true;
                            Output.WriteLine("{\"event\":\"save\"}");
                        }
                        else if (ctrl && e.VirtualKey == 0x4F)
                        {
                            e.Handled = true;
                            Output.WriteLine("{\"event\":\"open\"}");
                        }
                    };
                    web.NavigationCompleted += (sender, e) =>
                    {
                        if (!e.IsSuccess)
                        {
                            Console.Error.WriteLine("Navigation failed: " + e.WebErrorStatus);
                            context.ExitThread();
                        }
                    };
                    web.SetVirtualHostNameToFolderMapping("sizing.local", args[1], CoreWebView2HostResourceAccessKind.Deny);
                    web.Navigate(Page);
                }
                catch (Exception e)
                {
                    Console.Error.WriteLine(e);
                    context.ExitThread();
                }
            }));
            Application.Run(context);
            if (controller != null) controller.Close();
        }
    }
}
