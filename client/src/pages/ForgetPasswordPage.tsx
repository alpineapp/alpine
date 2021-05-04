import React from 'react';
import {
    Box,
    Heading,
    useColorModeValue,
} from '@chakra-ui/react'
import { Card } from '../components/Card';
import { ForgetPasswordForm } from '../components/AuthForm/ForgetPasswordForm'

interface ForgetPasswordPageProps {

}

const ForgetPasswordPage: React.FC<ForgetPasswordPageProps> = () => {
    return (
      <Box
        bg={useColorModeValue('gray.50', 'inherit')}
        minH="100vh"
        py="12"
        px={{ base: '4', lg: '8' }}
      >
        <Box maxW="md" mx="auto">
          <Box>Logo Placeholder</Box>
          <Heading textAlign="center" size="xl" fontWeight="extrabold">
            Reset Your Password
          </Heading>
          <Card mt="8">
            <ForgetPasswordForm />
          </Card>
        </Box>
      </Box>

    );
}

export default ForgetPasswordPage;